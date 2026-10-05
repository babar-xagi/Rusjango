use crate::project::{find_project_root, settings_path, template, APP_API};
use crate::settings::{database_enabled, installed_apps, replace_database};
use anyhow::{bail, Result};
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
    let settings_path = settings_path(&root)?;
    let content = fs::read_to_string(&settings_path)?;
    let apps = list_installed_apps(&settings_path)?;

    if !database_enabled(&content)? {
        fs::write(
            &settings_path,
            replace_database(&content, DATABASE_BLOCK.split_once("= ").unwrap().1)?,
        )?;
    }

    let migrations = root.join("migrations");
    fs::create_dir_all(&migrations)?;
    let gitkeep = migrations.join(".gitkeep");
    if !gitkeep.exists() {
        fs::write(gitkeep, "")?;
    }

    for app in apps {
        let app_dir = root.join("apps").join(&app);
        if !app_dir.is_dir() {
            continue;
        }
        scaffold_app(&app_dir, &app)?;
    }

    println!("ORM enabled.");
    println!("  DATABASE configured (SQLite: db.sqlite3)");
    println!("  migrations/ created");
    println!("  models.py / schemas.py added to apps (where missing)");
    println!("  Untouched starter APIs upgraded; custom APIs preserved");
    println!();
    println!("Next steps:");
    println!("  rusjango migrate   — create tables");
    println!("  rusjango dev       — start server");
    Ok(())
}

pub fn remove_orm(yes: bool) -> Result<()> {
    let root = find_project_root(Path::new("."))?;
    let settings_path = settings_path(&root)?;
    let content = fs::read_to_string(&settings_path)?;

    if !database_enabled(&content)? {
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

    let new_content = replace_database(&content, "None")?;
    fs::write(&settings_path, new_content)?;
    println!("ORM disabled (DATABASE = None).");
    Ok(())
}

fn list_installed_apps(settings_path: &Path) -> Result<Vec<String>> {
    let content = fs::read_to_string(settings_path)?;
    Ok(installed_apps(&content)?
        .into_iter()
        .filter_map(|app| app.strip_prefix("apps.").map(str::to_string))
        .collect())
}

fn copy_template_file(name: &str, dst: &Path, app_name: &str) -> Result<()> {
    let raw = template(name)?;
    let rendered = raw.replace("{{ app_name }}", app_name);
    fs::write(dst, rendered)?;
    Ok(())
}

pub fn scaffold_app(app_dir: &Path, app_name: &str) -> Result<()> {
    for name in ["models.py", "schemas.py"] {
        let dst = app_dir.join(name);
        if !dst.exists() {
            copy_template_file(&format!("orm/{name}"), &dst, app_name)?;
        }
    }
    let api = app_dir.join("api.py");
    if api.exists() && fs::read_to_string(&api)?.trim() == APP_API.trim() {
        copy_template_file("orm/api_with_orm.py", &api, app_name)?;
    }
    Ok(())
}

fn rusjango_src_on_path(project_root: &Path) -> Option<std::ffi::OsString> {
    for ancestor in project_root.ancestors() {
        let candidate = ancestor.join("python").join("rusjango").join("src");
        if candidate.is_dir() {
            let mut paths = vec![candidate];
            if let Some(existing) = std::env::var_os("PYTHONPATH") {
                paths.extend(std::env::split_paths(&existing));
            }
            return std::env::join_paths(paths).ok();
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
    match cmd.status() {
        Ok(status) => {
            if status.success() {
                return Ok(());
            }
            bail!("Migration process failed with {status}");
        }
        Err(err) if err.kind() == io::ErrorKind::NotFound => {}
        Err(err) => return Err(err.into()),
    }
    let mut fallback = std::process::Command::new("python");
    fallback
        .args(["-m", "rusjango._migrate"])
        .current_dir(&root);
    if let Some(src) = rusjango_src_on_path(&root) {
        fallback.env("PYTHONPATH", src);
    }
    let status = fallback.status()?;
    if !status.success() {
        bail!("Migration process failed with {status}");
    }
    Ok(())
}
