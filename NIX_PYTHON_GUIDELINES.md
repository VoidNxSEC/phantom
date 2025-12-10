# Nix + Python Development Guidelines

## 📋 Common Pitfalls & Best Practices

### 1. **Python Standard Library Modules**

❌ **NEVER** include Python stdlib modules in `pythonPackages`:

```nix
# ❌ WRONG - These are stdlib modules
pythonEnv = pkgs.python3.withPackages (ps: with ps; [
  hashlib      # stdlib - SHA256, BLAKE2, etc.
  json         # stdlib - JSON parsing
  os           # stdlib - OS interface
  sys          # stdlib - System parameters
  re           # stdlib - Regular expressions
  datetime     # stdlib - Date/time handling
  collections  # stdlib - Container datatypes
  typing       # stdlib - Type hints
  dataclasses  # stdlib (Python 3.7+)
  pathlib      # stdlib - Object-oriented filesystem paths
  subprocess   # stdlib - Process management
  threading    # stdlib - Thread-based parallelism
  queue        # stdlib - Synchronized queue classes
  tempfile     # stdlib - Temporary files
  struct       # stdlib - Binary data packing
  enum         # stdlib - Enumerations
  math         # stdlib - Mathematical functions
  time         # stdlib - Time access and conversions
  uuid         # stdlib - UUID generation
  base64       # stdlib - Base64 encoding
  mimetypes    # stdlib - MIME type mapping
]);

# ✅ CORRECT - Only external packages
pythonEnv = pkgs.python3.withPackages (ps: with ps; [
  pandas        # External package
  numpy         # External package
  requests      # External package
]);
```

**Full list of stdlib modules to AVOID:**
```
hashlib, json, os, sys, re, datetime, collections, typing, dataclasses,
pathlib, subprocess, threading, queue, tempfile, struct, enum, math,
time, uuid, base64, mimetypes, shutil, io, functools, itertools,
contextlib, warnings, logging, unittest, multiprocessing, concurrent,
asyncio, socket, ssl, http, urllib, email, csv, sqlite3, pickle, copy,
string, random, statistics, decimal, fractions, codecs, unicodedata
```

---

### 2. **Package Naming Conventions**

Package names in nixpkgs often differ from PyPI. **Always use lowercase** and check nixpkgs first:

```nix
# ❌ WRONG - PyPI-style names
pythonEnv = pkgs.python3.withPackages (ps: with ps; [
  vaderSentiment      # ❌ Wrong case
  Pillow              # ❌ Wrong case
  PyYAML              # ❌ Wrong case
  BeautifulSoup4      # ❌ Wrong case
]);

# ✅ CORRECT - nixpkgs naming
pythonEnv = pkgs.python3.withPackages (ps: with ps; [
  vadersentiment      # ✅ Lowercase
  pillow              # ✅ Lowercase
  pyyaml              # ✅ Lowercase
  beautifulsoup4      # ✅ Lowercase
]);
```

**Quick check command:**
```bash
# Search for a package
nix search nixpkgs#python3Packages.<package-name>

# Example:
nix search nixpkgs#python3Packages.vadersentiment
```

---

### 3. **Nix Multi-line String Escaping**

When embedding Python code in Nix `''` strings, **escape Python empty string literals**:

```nix
# ❌ WRONG - Breaks Nix parsing
phantomScript = pkgs.writeScriptBin "phantom" ''
  with open(filepath, 'rb') as f:
      for chunk in iter(lambda: f.read(65536), b''):  # ❌ b'' breaks Nix
          sha256_hash.update(chunk)
'';

# ✅ CORRECT - Escape with triple quotes
phantomScript = pkgs.writeScriptBin "phantom" ''
  with open(filepath, 'rb') as f:
      for chunk in iter(lambda: f.read(65536), b'''):  # ✅ b''' is correct
          sha256_hash.update(chunk)
'';
```

**Nix Escaping Rules for `''` strings:**
- `''` (two single quotes) → Use `'''` (three single quotes)
- `${var}` → Use `''${var}` to escape variable interpolation
- `\` → Use `\\` or just `\` (usually safe)

---

### 4. **NLP Stack: NLTK + spaCy (Recommended)**

**Deprecated/Unavailable packages:**
- ❌ `vadersentiment` - Often has dependency conflicts
- ❌ `textblob` - Outdated, poor performance
- ❌ Legacy sentiment libraries

**✅ Modern NLP Stack:**

```nix
pythonEnv = pkgs.python3.withPackages (ps: with ps; [
  # Core NLP
  nltk                # VADER sentiment, tokenization
  spacy               # Industrial-grade NLP
  scikit-learn        # ML algorithms
  
  # Language models (optional)
  # Download separately with: python -m spacy download en_core_web_sm
]);
```

**If you need specific spaCy models or custom packages, use overlay:**

```nix
{
  outputs = { self, nixpkgs, ... }:
    let
      pkgs = import nixpkgs {
        inherit system;
        overlays = [
          (final: prev: {
            python3 = prev.python3.override {
              packageOverrides = pyFinal: pyPrev: {
                # Custom package or override
                my-nlp-package = pyPrev.buildPythonPackage {
                  pname = "my-nlp-package";
                  version = "1.0.0";
                  src = fetchPypi { ... };
                  propagatedBuildInputs = with pyFinal; [ nltk spacy ];
                };
              };
            };
          })
        ];
      };
    in { ... };
}
```

---

### 5. **Variable Scoping in Nix**

Define constants in the `let` block, not inside Python strings:

```nix
# ❌ WRONG - VERSION undefined in Nix scope
{
  outputs = { self, nixpkgs, ... }:
    let
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.default = pkgs.mkShell {
        shellHook = ''
          export APP_VERSION="${VERSION}"  # ❌ VERSION not defined
        '';
      };
    };
}

# ✅ CORRECT - Define in let block
{
  outputs = { self, nixpkgs, ... }:
    let
      VERSION = "2.0.0";  # ✅ Defined in Nix scope
      
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.default = pkgs.mkShell {
        shellHook = ''
          export APP_VERSION="${VERSION}"  # ✅ Works
        '';
      };
    };
}
```

---

### 6. **Handling Dependency Conflicts**

When packages have conflicting dependencies (e.g., `typer` versions):

```nix
{
  overlays = [
    (final: prev: {
      python3 = prev.python3.override {
        packageOverrides = pyFinal: pyPrev: {
          # Force specific version or alias
          typer-slim = pyPrev.typer;
          
          # Override package to accept aliased dependency
          weasel = pyPrev.weasel.overridePythonAttrs (old: {
            pythonRuntimeDepsCheck = false;  # Disable strict checks
            propagatedBuildInputs = old.propagatedBuildInputs ++ [
              pyFinal.typer-slim  # Use aliased version
            ];
          });
        };
      };
    })
  ];
}
```

---

### 7. **Testing Your Flake**

Before committing, always test:

```bash
# Check syntax
nix flake check

# Test dev shell
nix develop --command python --version

# Test build (if applicable)
nix build

# Search for packages
nix search nixpkgs#python3Packages | grep <package>
```

---

### 8. **Quick Reference: Safe Python Packages**

**✅ Safe to use (verified in nixpkgs):**

```nix
pythonEnv = pkgs.python3.withPackages (ps: with ps; [
  # Data Science
  pandas
  numpy
  scipy
  matplotlib
  seaborn
  plotly
  
  # NLP
  nltk
  spacy
  scikit-learn
  transformers  # HuggingFace
  
  # Web
  requests
  flask
  fastapi
  aiohttp
  
  # Database
  sqlalchemy
  psycopg2
  pymongo
  
  # Utilities
  click          # CLI framework
  pydantic       # Data validation
  pytest         # Testing
  black          # Code formatter
  mypy           # Type checker
  
  # File Processing
  pillow         # Image processing
  openpyxl       # Excel files
  pyyaml         # YAML
  python-magic   # MIME detection
  
  # Crypto & Security
  cryptography
  pynacl
  pyotp
]);
```

---

### 9. **Common Error Messages & Solutions**

#### Error: `undefined variable 'X'`
```
error: undefined variable 'hashlib'
```
**Solution:** Remove from `pythonPackages` - it's a stdlib module.

---

#### Error: `syntax error, unexpected ')'`
```
error: syntax error, unexpected ')', expecting ';'
       for chunk in iter(lambda: f.read(65536), b''):
```
**Solution:** Escape Python `b''` as `b'''` in Nix strings.

---

#### Error: `attribute 'vaderSentiment' missing`
```
error: attribute 'vaderSentiment' missing
```
**Solution:** Use lowercase: `vadersentiment`

---

### 10. **Project Structure Recommendation**

```
project/
├── flake.nix              # Main flake
├── flake.lock            # Locked dependencies
├── NIX_PYTHON_GUIDELINES.md  # This file
├── overlays/             # Custom overlays
│   └── python-packages.nix
├── packages/             # Custom packages
│   └── my-nlp-tool/
│       └── default.nix
└── src/                  # Python source
    └── main.py
```

---

## 🎯 Best Practices Summary

1. ✅ **Never** include stdlib modules in `pythonPackages`
2. ✅ **Always** use lowercase package names
3. ✅ **Escape** `b''` as `b'''` in Nix multi-line strings
4. ✅ **Define** constants in Nix `let` blocks
5. ✅ **Test** with `nix flake check` before committing
6. ✅ **Use** NLTK + spaCy for NLP (not deprecated libs)
7. ✅ **Search** nixpkgs before assuming package name
8. ✅ **Prefer** overlays for complex dependency management

---

## 📚 Resources

- [Nixpkgs Python Packages](https://search.nixos.org/packages?channel=unstable&query=python3Packages)
- [Nix Pills - Developing with nix-shell](https://nixos.org/guides/nix-pills/developing-with-nix-shell.html)
- [Python on Nix](https://nixos.wiki/wiki/Python)
- [Nix String Escaping](https://nix.dev/manual/nix/2.18/language/values.html#type-string)

---

**Last Updated:** 2025-12-10  
**Maintainer:** Phantom Project Team
