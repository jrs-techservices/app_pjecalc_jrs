@echo off
rem Sobe o servico HTTP da automacao PJe-Calc e o reinicia se cair.
rem Rode na sessao do usuario logado (o PJe-Calc precisa estar aberto nela).
cd /d "%~dp0"
chcp 65001 >nul
if not exist logs mkdir logs
set PYTHON=env\Scripts\python.exe

:loop
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
"%PYTHON%" server.py >> "logs\servico_%TS%.log" 2>&1
if %ERRORLEVEL%==2 goto configuracao
if %ERRORLEVEL%==3 goto ja_rodando
echo Servico encerrado. Reiniciando em 10 s...
timeout /t 10 /nobreak >nul
goto loop

:configuracao
echo Configuracao incompleta: defina PJECALC_API_TOKEN no .env. Veja logs\servico_%TS%.log
pause
exit /b 2

:ja_rodando
echo O servico ja esta rodando nesta maquina.
exit /b 3
