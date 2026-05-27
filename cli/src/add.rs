use crate::project::{copy_template_tree, find_project_root, templates_dir};
use crate::settings::{add_installed_app, ensure_main_loads_apps};
use anyhow::{bail, Result};
use std::fs;
use std::path::Path;

pub fn validate_app_name(name: &str) -> Result<()> {
    if name.is_empty() {
        bail!("App name cannot be empty");
    }
    let mut chars = name.chars();
    let Some(first) = chars.next() else {
        bail!("App name cannot be empty");
    };
    if !first.is_ascii_alphabetic() && first != '_' {
        bail!("App name must start with a letter or underscore");
    }
    if !name.chars().all(|c| c.is_ascii_alphanumeric() || c == '_') {
        bail!("App name may only contain letters, numbers, and underscores");
    }
    if name == "apps" || name == "rusjango" {
        bail!("'{name}' is a reserved name");
    }
    Ok(())
}

pub fn run(name: &str) -> Result<()> {
    validate_app_name(name)?;

    let root = find_project_root(Path::new("."))?;
    let apps_root = root.join("apps");
    let app_dir = apps_root.join(name);

    if app_dir.exists() {
        bail!("App already exists: {}", app_dir.display());
    }

    let template_root = templates_dir().join("app");
    if !template_root.is_dir() {
        bail!("App templates not found at {}", template_root.display());
    }

    fs::create_dir_all(&apps_root)?;
    let apps_init = apps_root.join("__init__.py");
    if !apps_init.exists() {
        fs::write(&apps_init, "# Rusjango applications\n")?;
    }
    copy_template_tree(&template_root, &app_dir, name, "")?;

    let module = format!("apps.{name}");
    let settings_path = root.join("settings.py");
    add_installed_app(&settings_path, &module)?;

    let main_path = root.join("main.py");
    if main_path.is_file() {
        ensure_main_loads_apps(&main_path)?;
    }

    println!("Added app '{name}'");
    println!("  Package: apps/{name}/");
    println!("  Registered: INSTALLED_APPS += \"{module}\"");
    println!("  Routes: /api/{name}/... (see apps/{name}/api.py)");
    Ok(())
}
