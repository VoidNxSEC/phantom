{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python3
    ripgrep
    jq
  ];
  
  shellHook = ''
    echo "Pipeline environment loaded"
  '';
}
