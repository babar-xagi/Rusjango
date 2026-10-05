//! Edit literal settings while preserving the rest of the Python file.

use anyhow::{bail, Context, Result};
use regex::Regex;
use std::fs;
use std::ops::Range;
use std::path::Path;

const LOAD_APPS_LINE: &str = "app.load_installed_apps()";

fn apps_value(content: &str) -> Result<(Range<usize>, Vec<String>)> {
    if Regex::new(r"(?m)^INSTALLED_APPS[ \t]*=")?
        .find_iter(content)
        .count()
        != 1
    {
        bail!("Expected one top-level INSTALLED_APPS assignment");
    }
    let re = Regex::new(r"(?ms)^INSTALLED_APPS[ \t]*=[ \t]*\[(.*?)\]")?;
    let captures = re
        .captures(content)
        .context("INSTALLED_APPS must be a literal list")?;
    let body = captures.get(1).unwrap();
    let suffix = content[body.end() + 1..]
        .lines()
        .next()
        .unwrap_or("")
        .trim();
    if !suffix.is_empty() && !suffix.starts_with('#') {
        bail!("INSTALLED_APPS must be a literal list");
    }
    let bytes = body.as_str().as_bytes();
    let mut items = Vec::new();
    let mut i = 0;
    while i < bytes.len() {
        match bytes[i] {
            b' ' | b'\t' | b'\r' | b'\n' | b',' => i += 1,
            b'#' => {
                while i < bytes.len() && bytes[i] != b'\n' {
                    i += 1;
                }
            }
            quote @ (b'\'' | b'"') => {
                i += 1;
                let start = i;
                while i < bytes.len() && bytes[i] != quote {
                    i += 1;
                }
                if i == bytes.len() {
                    bail!("Unclosed app name");
                }
                let item = &body.as_str()[start..i];
                if !item
                    .chars()
                    .all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '.')
                {
                    bail!("Unsupported app name in INSTALLED_APPS");
                }
                items.push(item.to_string());
                i += 1;
            }
            _ => bail!("INSTALLED_APPS must contain literal strings"),
        }
    }
    Ok((body.start() - 1..body.end() + 1, items))
}

pub fn installed_apps(content: &str) -> Result<Vec<String>> {
    Ok(apps_value(content)?.1)
}

fn render_apps(items: &[String]) -> String {
    if items.is_empty() {
        return "[]".to_string();
    }
    format!(
        "[\n{}]",
        items
            .iter()
            .map(|item| format!("    \"{item}\",\n"))
            .collect::<String>()
    )
}

pub fn add_installed_app(settings_path: &Path, module: &str) -> Result<()> {
    let mut content = fs::read_to_string(settings_path)?;
    let (range, mut apps) = apps_value(&content)?;
    if !apps.iter().any(|item| item == module) {
        apps.push(module.to_string());
        content.replace_range(range, &render_apps(&apps));
        fs::write(settings_path, content)?;
    }
    Ok(())
}

pub fn remove_installed_app(settings_path: &Path, module: &str) -> Result<()> {
    let mut content = fs::read_to_string(settings_path)?;
    let (range, mut apps) = apps_value(&content)?;
    if !apps.iter().any(|item| item == module) {
        bail!("App {module:?} is not registered");
    }
    apps.retain(|item| item != module);
    content.replace_range(range, &render_apps(&apps));
    fs::write(settings_path, content)?;
    Ok(())
}

fn database_value(content: &str) -> Result<Range<usize>> {
    let re = Regex::new(r"(?m)^DATABASE[ \t]*=[ \t]*")?;
    if re.find_iter(content).count() != 1 {
        bail!("Expected one top-level DATABASE assignment");
    }
    let start = re
        .find(content)
        .context("Could not find DATABASE assignment")?
        .end();
    let bytes = content.as_bytes();
    if content[start..].starts_with("None") {
        let end = start + 4;
        let suffix = content[end..].lines().next().unwrap_or("").trim();
        if !suffix.is_empty() && !suffix.starts_with('#') {
            bail!("DATABASE must be None or a dictionary");
        }
        return Ok(start..end);
    }
    if bytes.get(start) != Some(&b'{') {
        bail!("DATABASE must be None or a dictionary");
    }
    let mut depth = 0;
    let mut quote = None;
    let mut escaped = false;
    let mut comment = false;
    for (offset, &byte) in bytes[start..].iter().enumerate() {
        if comment {
            if byte == b'\n' {
                comment = false;
            }
            continue;
        }
        if let Some(delimiter) = quote {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == delimiter {
                quote = None;
            }
            continue;
        }
        match byte {
            b'\'' | b'"' => quote = Some(byte),
            b'#' => comment = true,
            b'{' => depth += 1,
            b'}' => {
                depth -= 1;
                if depth == 0 {
                    let end = start + offset + 1;
                    let suffix = content[end..].lines().next().unwrap_or("").trim();
                    if !suffix.is_empty() && !suffix.starts_with('#') {
                        bail!("DATABASE must be a literal dictionary");
                    }
                    return Ok(start..end);
                }
            }
            _ => {}
        }
    }
    bail!("Unclosed DATABASE dictionary")
}

pub fn database_enabled(content: &str) -> Result<bool> {
    Ok(&content[database_value(content)?] != "None")
}

pub fn replace_database(content: &str, value: &str) -> Result<String> {
    let mut updated = content.to_string();
    updated.replace_range(database_value(content)?, value);
    Ok(updated)
}

pub fn ensure_main_loads_apps(main_path: &Path) -> Result<()> {
    let content = fs::read_to_string(main_path)?;
    if !content.contains(LOAD_APPS_LINE) {
        fs::write(
            main_path,
            format!(
                "{}\n\n# Load routers from INSTALLED_APPS\n{LOAD_APPS_LINE}\n",
                content.trim_end()
            ),
        )?;
    }
    Ok(())
}

pub fn remove_main_loads_apps(main_path: &Path) -> Result<()> {
    let content = fs::read_to_string(main_path)?;
    let pattern = Regex::new(
        r"(?m)^# Load routers from INSTALLED_APPS[ \t]*\napp\.load_installed_apps\(\)[ \t]*\n?",
    )?;
    fs::write(main_path, pattern.replace_all(&content, "").as_ref())?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn preserves_other_settings_when_adding_second_app() {
        let source = "DEBUG = True\nINSTALLED_APPS = ['apps.alpha']\nDATABASE = None\n";
        let (range, mut apps) = apps_value(source).unwrap();
        apps.push("apps.beta".to_string());
        let mut updated = source.to_string();
        updated.replace_range(range, &render_apps(&apps));
        assert!(updated.starts_with("DEBUG = True\n"));
        assert!(updated.ends_with("DATABASE = None\n"));
        assert_eq!(
            installed_apps(&updated).unwrap(),
            vec!["apps.alpha", "apps.beta"]
        );
    }

    #[test]
    fn nested_database_removal_preserves_following_settings() {
        let source = "DATABASE = {\"OPTIONS\": {\"text\": \"}\"}}\nAUTH = None\n";
        assert_eq!(
            replace_database(source, "None").unwrap(),
            "DATABASE = None\nAUTH = None\n"
        );
    }

    #[test]
    fn refuses_computed_settings() {
        assert!(apps_value("INSTALLED_APPS = [load_apps()]\n").is_err());
        assert!(database_value("DATABASE = None if DEBUG else config\n").is_err());
        assert!(database_value("DATABASE = {} | config\n").is_err());
    }
}
