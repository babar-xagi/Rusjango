use anyhow::{bail, Result};
use std::fs;
use std::path::{Path, PathBuf};

/// Directory containing `project/` and `app/` templates (monorepo layout).
pub fn templates_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../templates")
}

pub fn find_project_root(start: &Path) -> Result<PathBuf> {
    let mut current = start.canonicalize().unwrap_or_else(|_| start.to_path_buf());
    loop {
        let pyproject = current.join("pyproject.toml");
        if pyproject.is_file() && has_rusjango_tool(&pyproject)? {
            return Ok(current);
        }
        if !current.pop() {
            bail!("No Rusjango project found (missing [tool.rusjango] in pyproject.toml)");
        }
    }
}

fn has_rusjango_tool(pyproject: &Path) -> Result<bool> {
    let content = fs::read_to_string(pyproject)?;
    Ok(content.contains("[tool.rusjango]"))
}

pub fn validate_project_name(name: &str) -> Result<()> {
    if name.is_empty() {
        bail!("Project name cannot be empty");
    }
    if !name
        .chars()
        .all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-')
    {
        bail!("Project name may only contain letters, numbers, hyphens, and underscores");
    }
    Ok(())
}

pub fn render_template(content: &str, project_name: &str, secret_key: &str) -> String {
    content
        .replace("{{ project_name }}", project_name)
        .replace("{{ app_name }}", project_name)
        .replace("{{ secret_key }}", secret_key)
}

pub fn copy_template_tree(
    src: &Path,
    dst: &Path,
    project_name: &str,
    secret_key: &str,
) -> Result<()> {
    fs::create_dir_all(dst)?;
    for entry in fs::read_dir(src)? {
        let entry = entry?;
        let name = entry.file_name();
        let name_str = name.to_string_lossy();
        let src_path = entry.path();
        let is_tpl = name_str.ends_with(".tpl");
        let out_name = if is_tpl {
            name_str.trim_end_matches(".tpl").to_string()
        } else {
            name_str.to_string()
        };
        let dst_path = dst.join(&out_name);
        if src_path.is_dir() {
            copy_template_tree(&src_path, &dst_path, project_name, secret_key)?;
        } else {
            let raw = fs::read_to_string(&src_path)?;
            let rendered = render_template(&raw, project_name, secret_key);
            fs::write(&dst_path, rendered)?;
        }
    }
    Ok(())
}

pub fn generate_secret_key() -> String {
    use rand::Rng;
    const CHARSET: &[u8] =
        b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)";
    let mut rng = rand::thread_rng();
    (0..50)
        .map(|_| {
            let idx = rng.gen_range(0..CHARSET.len());
            CHARSET[idx] as char
        })
        .collect()
}
