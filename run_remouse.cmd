@echo off
REM Script pour lancer remarkable_mouse avec les bons arguments et le bon Python
setlocal
set PYTHON_EXE=C:\Users\fdonc\AppData\Local\Programs\Python\Python313\python.exe
set PROJECT_DIR=%~dp0

pushd "%PROJECT_DIR%" >nul
"%PYTHON_EXE%" -m remarkable_mouse.remarkable_mouse --password laZ5cOuyfv --pen %*
popd >nul
