use anyhow::{bail, Context, Result};
use regex::Regex;
use std::fs;
use std::path::Path;

const LOAD_APPS_LINE: &str = "app.load_installed_apps()";

pub fn add_installed_app(settings_path: &Path, module: &str) -> Result<()> {
    let content = fs::read_to_string(settings_path)
        .with_context(|| format!("read {}", settings_path.display()))?;

    if content.contains(&format!("\"{module}\"")) {
        return Ok(());
    }

    let new_content = if let Some(caps) =
        Regex::new(r"(?m)^(INSTALLED_APPS\s*=\s*)\[\s*\]\s*$")?.captures(&content)
    {
        let indent = "    ";
        content.replace(
            caps.get(0).unwrap().as_str(),
            &format!(
                "{}[\n{indent}\"{module}\",\n]",
                caps.get(1).unwrap().as_str(),
            ),
        )
    } else if let Some(caps) =
        Regex::new(r"(?ms)^(INSTALLED_APPS\s*=\s*\[)(.*?)(\n\])")?.captures(&content)
    {
        let prefix = caps.get(1).unwrap().as_str();
        let body = caps.get(2).unwrap().as_str();
        let suffix = caps.get(3).unwrap().as_str();
        let entry = format!("    \"{module}\",\n");
        format!("{prefix}{body}{entry}{suffix}")
    } else {
        bail!(
            "Could not find INSTALLED_APPS in {}",
            settings_path.display()
        )
    };

    fs::write(settings_path, new_content)?;
    Ok(())
}

pub fn remove_installed_app(settings_path: &Path, module: &str) -> Result<()> {
    let content = fs::read_to_string(settings_path)?;

    if !content.contains(&format!("\"{module}\"")) {
        bail!("App {module:?} is not registered in INSTALLED_APPS");
    }

    let line_pattern = Regex::new(&format!(r#"(?m)^\s*"{}"?,?\s*\n"#, regex::escape(module)))?;
    let new_content = line_pattern.replace_all(&content, "").to_string();

    let new_content = Regex::new(r"(?m)^INSTALLED_APPS\s*=\s*\[\s*\n\s*\]")?
        .replace(&new_content, "INSTALLED_APPS = []")
        .to_string();

    fs::write(settings_path, new_content)?;
    Ok(())
}

pub fn ensure_main_loads_apps(main_path: &Path) -> Result<()> {
    let content = fs::read_to_string(main_path)?;
    if content.contains(LOAD_APPS_LINE) {
        return Ok(());
    }
    let mut updated = content.trim_end().to_string();
    updated.push_str("\n\n\n");
    updated.push_str("# Load routers from INSTALLED_APPS\n");
    updated.push_str(LOAD_APPS_LINE);
    updated.push('\n');
    fs::write(main_path, updated)?;
    Ok(())
}

pub fn remove_main_loads_apps(main_path: &Path) -> Result<()> {
    let content = fs::read_to_string(main_path)?;
    let pattern = Regex::new(
        r"(?m)^# Load routers from INSTALLED_APPS\s*\napp\.load_installed_apps\(\)\s*\n?",
    )?;
    if pattern.is_match(&content) {
        fs::write(main_path, pattern.replace_all(&content, "").to_string())?;
    }
    Ok(())
}
