use anyhow::{bail, Result};
use std::fs;
use std::path::{Path, PathBuf};

/// Templates travel with the installed binary, independent of the checkout.
pub const APP_API: &str = include_str!("../../templates/app/api.py.tpl");

pub fn template(name: &str) -> Result<&'static str> {
    Ok(match name {
        "project/main.py" => include_str!("../../templates/project/main.py.tpl"),
        "project/settings.py" => include_str!("../../templates/project/settings.py.tpl"),
        "project/pyproject.toml" => include_str!("../../templates/project/pyproject.toml.tpl"),
        "app/__init__.py" => include_str!("../../templates/app/__init__.py.tpl"),
        "app/api.py" => APP_API,
        "orm/models.py" => include_str!("../../templates/orm/models.py.tpl"),
        "orm/schemas.py" => include_str!("../../templates/orm/schemas.py.tpl"),
        "orm/api_with_orm.py" => include_str!("../../templates/orm/api_with_orm.py.tpl"),
        _ => bail!("Unknown template: {name}"),
    })
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
    let config: toml::Value = toml::from_str(&content)?;
    Ok(config
        .get("tool")
        .and_then(|tool| tool.get("rusjango"))
        .is_some())
}

pub fn settings_path(root: &Path) -> Result<PathBuf> {
    let config: toml::Value = toml::from_str(&fs::read_to_string(root.join("pyproject.toml"))?)?;
    let name = config
        .get("tool")
        .and_then(|tool| tool.get("rusjango"))
        .and_then(|config| config.get("settings"))
        .and_then(|name| name.as_str())
        .unwrap_or("settings.py");
    Ok(root.join(name))
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

pub fn write_templates(
    group: &str,
    dst: &Path,
    project_name: &str,
    secret_key: &str,
) -> Result<()> {
    fs::create_dir_all(dst)?;
    let files: &[&str] = match group {
        "project" => &["main.py", "settings.py", "pyproject.toml"],
        "app" => &["__init__.py", "api.py"],
        _ => bail!("Unknown template group: {group}"),
    };
    for name in files {
        let raw = template(&format!("{group}/{name}"))?;
        fs::write(
            dst.join(name),
            render_template(raw, project_name, secret_key),
        )?;
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn embedded_templates_render_without_checkout() {
        let rendered = render_template(template("project/settings.py").unwrap(), "demo", "secret");
        assert!(rendered.contains("APP_NAME = \"demo\""));
        assert!(!rendered.contains("{{"));
    }
}
