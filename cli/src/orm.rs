use crate::project::{find_project_root, templates_dir};
use anyhow::{bail, Result};
use regex::Regex;
use std::fs;
use std::io::{self, Write};
use std::path::Path;

const DATABASE_BLOCK: &str = r#"DATABASE = {
    "ENGINE": "sqlite",
    "NAME": "db.sqlite3",
    "ASYNC": True,
}"#;

pub fn add_orm() -> Result<()> {
    let root = find_project_root(Path::new("."))?;
    let settings_path = root.join("settings.py");
    let content = fs::read_to_string(&settings_path)?;

    if content.contains("DATABASE = {") && !content.contains("DATABASE = None") {
        println!("ORM already enabled (DATABASE is configured).");
        return Ok(());
    }

    let new_content = if content.contains("DATABASE = None") {
        content.replace("DATABASE = None", DATABASE_BLOCK)
    } else {
        bail!("Could not find DATABASE = None in settings.py");
    };
    fs::write(&settings_path, new_content)?;

    let migrations = root.join("migrations");
    fs::create_dir_all(&migrations)?;
    let gitkeep = migrations.join(".gitkeep");
    if !gitkeep.exists() {
        fs::write(gitkeep, "")?;
    }

    add_pyproject_orm_deps(&root.join("pyproject.toml"))?;

    let apps = list_installed_apps(&settings_path)?;
    let template_root = templates_dir().join("orm");
    for app in apps {
        let app_dir = root.join("apps").join(&app);
        if !app_dir.is_dir() {
            continue;
        }
        if !app_dir.join("models.py").exists() {
            copy_template_file(
                &template_root.join("models.py.tpl"),
                &app_dir.join("models.py"),
                &app,
            )?;
        }
        if !app_dir.join("schemas.py").exists() {
            copy_template_file(
                &template_root.join("schemas.py.tpl"),
                &app_dir.join("schemas.py"),
                &app,
            )?;
        }
        let api_path = app_dir.join("api.py");
        if api_path.exists() {
            let api = fs::read_to_string(&api_path)?;
            // Upgrade api.py only if it does not already import from the local models module.
            // This is safe for any app name.
            if !api.contains("from .models import") && !api.contains("from rusjango.orm import") {
                copy_template_file(&template_root.join("api_with_orm.py.tpl"), &api_path, &app)?;
            }
        }
    }

    println!("ORM enabled.");
    println!("  DATABASE configured (SQLite: db.sqlite3)");
    println!("  migrations/ created");
    println!("  models.py / schemas.py added to apps (where missing)");
    println!("  api.py upgraded with ORM routes (where not already done)");
    println!();
    println!("Next steps:");
    println!("  rusjango migrate   — create tables");
    println!("  rusjango dev       — start server");
    Ok(())
}

pub fn remove_orm(yes: bool) -> Result<()> {
    let root = find_project_root(Path::new("."))?;
    let settings_path = root.join("settings.py");
    let content = fs::read_to_string(&settings_path)?;

    if !content.contains("DATABASE = {") {
        println!("ORM is not enabled (DATABASE is None).");
        return Ok(());
    }

    if !yes {
        eprintln!("This will disable ORM and set DATABASE = None.");
        eprintln!("Model files and migrations/ will be kept.");
        eprint!("Continue? [y/N] ");
        io::stderr().flush()?;
        let mut line = String::new();
        io::stdin().read_line(&mut line)?;
        if !line.trim().eq_ignore_ascii_case("y") && !line.trim().eq_ignore_ascii_case("yes") {
            println!("Aborted.");
            return Ok(());
        }
    }

    let re = Regex::new(r"(?ms)^DATABASE = \{.*?\}\s*$")?;
    let new_content = re.replace(&content, "DATABASE = None").to_string();
    fs::write(&settings_path, new_content)?;
    println!("ORM disabled (DATABASE = None).");
    Ok(())
}

fn list_installed_apps(settings_path: &Path) -> Result<Vec<String>> {
    let content = fs::read_to_string(settings_path)?;
    let re = Regex::new(r#""apps\.([a-zA-Z0-9_]+)""#)?;
    Ok(re
        .captures_iter(&content)
        .filter_map(|c| c.get(1).map(|m| m.as_str().to_string()))
        .collect())
}

fn copy_template_file(src: &Path, dst: &Path, app_name: &str) -> Result<()> {
    let raw = fs::read_to_string(src)?;
    let rendered = raw.replace("{{ app_name }}", app_name);
    fs::write(dst, rendered)?;
    Ok(())
}

fn add_pyproject_orm_deps(pyproject: &Path) -> Result<()> {
    let content = fs::read_to_string(pyproject)?;
    if content.contains("aiosqlite") {
        return Ok(());
    }
    let re = Regex::new(r"(?m)^dependencies = \[")?;
    if re.is_match(&content) {
        let new_content = re.replace(&content, "dependencies = [\n    \"aiosqlite>=0.20\",");
        fs::write(pyproject, new_content.as_ref())?;
    }
    Ok(())
}

fn rusjango_src_on_path(project_root: &Path) -> Option<std::ffi::OsString> {
    for ancestor in project_root.ancestors() {
        let candidate = ancestor.join("python").join("rusjango").join("src");
        if candidate.is_dir() {
            return Some(candidate.as_os_str().to_os_string());
        }
    }
    None
}

pub fn run_migrate() -> Result<()> {
    let root = find_project_root(Path::new("."))?;
    let mut cmd = std::process::Command::new("uv");
    cmd.args(["run", "python", "-m", "rusjango._migrate"])
        .current_dir(&root);
    if let Some(src) = rusjango_src_on_path(&root) {
        cmd.env("PYTHONPATH", src);
    }
    if cmd.status()?.success() {
        return Ok(());
    }
    let mut fallback = std::process::Command::new("python");
    fallback
        .args(["-m", "rusjango._migrate"])
        .current_dir(&root);
    if let Some(src) = rusjango_src_on_path(&root) {
        fallback.env("PYTHONPATH", src);
    }
    fallback.status()?;
    Ok(())
}
