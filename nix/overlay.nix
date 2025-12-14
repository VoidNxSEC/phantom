# Phantom overlay for nixpkgs
final: prev: {
  phantom = prev.callPackage ./package.nix { };
  
  # Python package overlay
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
    (python-final: python-prev: {
      phantom = python-prev.callPackage ./package.nix { };
    })
  ];
}
