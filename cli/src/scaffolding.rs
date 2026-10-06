//! Shared templates and ownership-aware Docker/test scaffolding.

use crate::project::find_project_root;
use anyhow::{bail, Context, Result};
use serde_json::{json, Map, Value};
use std::fs;
use std::io::{self, Write};
use std::path::{Path, PathBuf};

const MANIFEST: &str = ".rusjango-features.json";
const DOCKER: &[(&str, &str)] = &[
    (
        "Dockerfile",
        include_str!("../../python/rusjango/src/rusjango/templates/docker/Dockerfile.tpl"),
    ),
    (
        "compose.yml",
        include_str!("../../python/rusjango/src/rusjango/templates/docker/compose.yml.tpl"),
    ),
    (
        ".dockerignore",
        include_str!("../../python/rusjango/src/rusjango/templates/docker/dockerignore.tpl"),
    ),
    (
        "settings_docker.py",
        include_str!("../../python/rusjango/src/rusjango/templates/docker/settings_docker.py.tpl"),
    ),
    (
        "docker_app.py",
        include_str!("../../python/rusjango/src/rusjango/templates/docker/docker_app.py.tpl"),
    ),
];
const TESTS: &[(&str, &str)] = &[
    (
        "tests/conftest.py",
        include_str!("../../python/rusjango/src/rusjango/templates/tests/conftest.py.tpl"),
    ),
    (
        "tests/test_health.py",
        include_str!("../../python/rusjango/src/rusjango/templates/tests/test_health.py.tpl"),
    ),
];

fn profile(feature: &str) -> Result<&'static [(&'static str, &'static str)]> {
    match feature {
        "docker" => Ok(DOCKER),
        "tests" => Ok(TESTS),
        _ => bail!("Unknown scaffold: {feature}"),
    }
}

fn safe_path(root: &Path, name: &str) -> Result<PathBuf> {
    let mut current = root.to_path_buf();
    for part in Path::new(name).components() {
        if !matches!(part, std::path::Component::Normal(_)) {
            bail!("Invalid scaffold path: {name}");
        }
        current.push(part);
        if current.is_symlink() {
            bail!("Refusing to edit a symlink: {name}");
        }
    }
    Ok(current)
}

fn load_manifest(root: &Path) -> Result<Value> {
    let path = safe_path(root, MANIFEST)?;
    if !path.exists() {
        return Ok(json!({"format": 1, "features": {}}));
    }
    let value: Value = serde_json::from_str(&fs::read_to_string(path)?)?;
    if value.get("format").and_then(Value::as_u64) != Some(1) {
        bail!("Invalid scaffold manifest format");
    }
    let features = value
        .get("features")
        .and_then(Value::as_object)
        .context("Invalid scaffold manifest features")?;
    for (feature, entries) in features {
        let entries = entries
            .as_object()
            .context("Invalid scaffold ownership entries")?;
        let templates = profile(feature)?;
        if entries.len() != templates.len()
            || !templates
                .iter()
                .all(|(name, _)| entries.get(*name).is_some_and(Value::is_string))
        {
            bail!("Invalid scaffold ownership entries");
        }
    }
    Ok(value)
}

fn save_manifest(root: &Path, value: &Value) -> Result<()> {
    let path = safe_path(root, MANIFEST)?;
    if value["features"].as_object().unwrap().is_empty() {
        if path.exists() {
            fs::remove_file(path)?;
        }
    } else {
        fs::write(path, serde_json::to_string_pretty(value)? + "\n")?;
    }
    Ok(())
}

pub fn add(feature: &str) -> Result<()> {
    let root = find_project_root(Path::new("."))?;
    let mut value = load_manifest(&root)?;
    if value["features"].get(feature).is_some() {
        println!("{feature} scaffold already tracked.");
        return Ok(());
    }
    if feature == "docker" {
        for alias in ["compose.yaml", "docker-compose.yml", "docker-compose.yaml"] {
            if root.join(alias).exists() {
                bail!("Existing Docker configuration preserved: {alias}");
            }
        }
    }
    let config: toml::Value = toml::from_str(&fs::read_to_string(root.join("pyproject.toml"))?)?;
    let project = config
        .get("tool")
        .and_then(|v| v.get("rusjango"))
        .and_then(toml::Value::as_table)
        .context("Invalid project configuration")?;
    for key in ["app", "settings"] {
        if project.get(key).is_some_and(|value| !value.is_str()) {
            bail!("Project settings/app paths must be strings");
        }
    }
    let app = config
        .get("tool")
        .and_then(|v| v.get("rusjango"))
        .and_then(|v| v.get("app"))
        .and_then(toml::Value::as_str)
        .unwrap_or("main:app");
    let settings = config
        .get("tool")
        .and_then(|v| v.get("rusjango"))
        .and_then(|v| v.get("settings"))
        .and_then(toml::Value::as_str)
        .unwrap_or("settings.py");
    if !app
        .split_once(':')
        .is_some_and(|(module, attribute)| !module.is_empty() && !attribute.is_empty())
    {
        bail!("Project app must use module:attribute syntax");
    }
    if !root.join(settings).is_file() {
        bail!("Project settings file does not exist");
    }
    let mut contents = Map::new();
    for (name, template) in profile(feature)? {
        let path = safe_path(&root, name)?;
        if path.exists() {
            bail!("Existing file preserved: {name}");
        }
        let content = template
            .replace("{{ settings_path }}", &serde_json::to_string(settings)?)
            .replace("{{ app_path }}", &serde_json::to_string(app)?);
        contents.insert((*name).to_string(), Value::String(content));
    }
    for (name, content) in &contents {
        let path = safe_path(&root, name)?;
        fs::create_dir_all(path.parent().unwrap())?;
        fs::write(path, content.as_str().unwrap())?;
    }
    value["features"][feature] = Value::Object(contents);
    save_manifest(&root, &value)?;
    println!("{feature} scaffold added.");
    if feature == "tests" {
        println!("Run: uv run --with pytest --with pytest-asyncio pytest tests");
    } else {
        println!("Set ALLOWED_HOSTS, then run: docker compose up --build");
    }
    Ok(())
}

pub fn remove(feature: &str, yes: bool) -> Result<()> {
    let root = find_project_root(Path::new("."))?;
    if !yes {
        eprint!("Remove unchanged generated {feature} files? [y/N] ");
        io::stderr().flush()?;
        let mut answer = String::new();
        io::stdin().read_line(&mut answer)?;
        if !matches!(answer.trim().to_lowercase().as_str(), "y" | "yes") {
            println!("Aborted.");
            return Ok(());
        }
    }
    let mut value = load_manifest(&root)?;
    let entries = value["features"]
        .get(feature)
        .and_then(Value::as_object)
        .context("No tracked scaffold found")?
        .clone();
    // Check all paths before deleting any file.
    for name in entries.keys() {
        safe_path(&root, name)?;
    }
    for (name, content) in entries {
        let path = safe_path(&root, &name)?;
        if path.exists() {
            if path.is_file() && fs::read(&path)? == content.as_str().unwrap().as_bytes() {
                fs::remove_file(path)?;
            } else {
                println!("Preserved modified file: {name}");
            }
        }
    }
    value["features"].as_object_mut().unwrap().remove(feature);
    save_manifest(&root, &value)?;
    let tests = root.join("tests");
    if feature == "tests" && tests.is_dir() && fs::read_dir(&tests)?.next().is_none() {
        fs::remove_dir(tests)?;
    }
    println!("{feature} scaffold removed.");
    Ok(())
}
