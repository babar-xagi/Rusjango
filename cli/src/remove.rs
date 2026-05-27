use crate::project::find_project_root;
use crate::settings::{remove_installed_app, remove_main_loads_apps};
use anyhow::{bail, Result};
use std::fs;
use std::io::{self, Write};
use std::path::Path;

pub fn run(name: &str, yes: bool) -> Result<()> {
    crate::add::validate_app_name(name)?;

    let root = find_project_root(Path::new("."))?;
    let app_dir = root.join("apps").join(name);
    let module = format!("apps.{name}");

    if !app_dir.is_dir() {
        bail!("App directory not found: {}", app_dir.display());
    }

    if !yes {
        eprintln!(
            "This will remove the '{name}' app and unregister it from settings.py."
        );
        eprint!("Do you want to continue? [y/N] ");
        io::stderr().flush()?;
        let mut line = String::new();
        io::stdin().read_line(&mut line)?;
        let answer = line.trim().to_lowercase();
        if answer != "y" && answer != "yes" {
            println!("Aborted.");
            return Ok(());
        }
    }

    let settings_path = root.join("settings.py");
    remove_installed_app(&settings_path, &module)?;

    fs::remove_dir_all(&app_dir)?;

    let main_path = root.join("main.py");
    if main_path.is_file() {
        let settings = fs::read_to_string(&settings_path)?;
        if !settings.contains("apps.") {
            remove_main_loads_apps(&main_path)?;
        }
    }

    println!("Removed app '{name}'");
    println!("  Deleted: apps/{name}/");
    println!("  Unregistered: \"{module}\" from INSTALLED_APPS");
    Ok(())
}
