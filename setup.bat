@echo off
echo ========================================
echo    Configuracao do Bot Clash Royale
echo ========================================
echo.

echo [1/4] Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale o Python 3.9+ primeiro.
    pause
    exit /b 1
)

echo.
echo [2/4] Verificando dependencias...
pip show clashroyalebuildabot >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando dependencias...
    pip install -e .
)

echo.
echo [3/4] Verificando ONNX Runtime...
pip show onnxruntime >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando ONNX Runtime...
    pip install onnxruntime==1.18.0
)

echo.
echo [4/4] Configuracao concluida!
echo.
echo ========================================
echo    PROXIMOS PASSOS:
echo ========================================
echo 1. Instale um emulador Android (BlueStacks, LDPlayer, etc.)
echo 2. Configure o emulador com resolucao 1920x1080
echo 3. Instale o Clash Royale no emulador
echo 4. Ative a depuracao USB no emulador
echo 5. Execute: python main.py
echo.
echo Consulte o arquivo SETUP_GUIDE.md para mais detalhes.
echo.
pause
