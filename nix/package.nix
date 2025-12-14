{ lib, python3Packages, fetchFromGitHub }:

python3Packages.buildPythonApplication rec {
  pname = "phantom";
  version = "2.0.0";
  format = "pyproject";

  src = ../.;

  nativeBuildInputs = with python3Packages; [
    hatchling
  ];

  propagatedBuildInputs = with python3Packages; [
    # Core
    pydantic
    rich
    typer
    
    # Data processing
    pandas
    numpy
    polars
    
    # NLP & ML
    sentence-transformers
    transformers
    tiktoken
    nltk
    scikit-learn
    
    # Vector DB
    faiss
    chromadb
    
    # HTTP & API
    requests
    httpx
    fastapi
    uvicorn
    
    # Utilities
    python-magic
    pyyaml
    psutil
    aiofiles
  ];

  pythonImportsCheck = [ "phantom" ];

  meta = with lib; {
    description = "AI-Powered Document Intelligence & Classification Pipeline";
    homepage = "https://github.com/kernelcore/phantom";
    license = licenses.mit;
    maintainers = [ ];
    mainProgram = "phantom";
  };
}
