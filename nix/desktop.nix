# Nix derivation for Phantom Desktop GTK4 application
{ lib
, python3Packages
, gtk4
, libadwaita
, wrapGAppsHook4
, gobject-introspection
}:

python3Packages.buildPythonApplication rec {
  pname = "phantom-desktop";
  version = "2.0.0";
  format = "other";  # Not a standard Python package

  src = ./..;

  nativeBuildInputs = [
    wrapGAppsHook4
    gobject-introspection
  ];

  buildInputs = [
    gtk4
    libadwaita
  ];

  propagatedBuildInputs = with python3Packages; [
    pygobject3
    pycairo
    # Phantom dependencies
    pydantic
    rich
  ];

  # No build step - just install
  dontBuild = true;

  installPhase = ''
    mkdir -p $out/bin $out/share/applications $out/share/phantom
    
    # Copy the main script
    cp apps/desktop/main.py $out/share/phantom/phantom-desktop.py
    
    # Create launcher script
    cat > $out/bin/phantom-desktop << EOF
    #!/usr/bin/env bash
    exec python3 $out/share/phantom/phantom-desktop.py "\$@"
    EOF
    chmod +x $out/bin/phantom-desktop
    
    # Desktop entry
    cat > $out/share/applications/dev.phantom.desktop.desktop << EOF
    [Desktop Entry]
    Name=Phantom Desktop
    Comment=AI-Powered Document Intelligence
    Exec=$out/bin/phantom-desktop
    Icon=utilities-system-monitor
    Type=Application
    Categories=Utility;Development;
    Terminal=false
    EOF
  '';

  meta = with lib; {
    description = "Phantom Desktop - Native GTK4 Document Intelligence";
    homepage = "https://github.com/kernelcore/phantom";
    license = licenses.asl20;
    maintainers = [ ];
    mainProgram = "phantom-desktop";
    platforms = platforms.linux;
  };
}
