***Antes de clonar o repositorio certifique-se de:***

> Ter o Build Tools e o Cx_Oracle baixados no seu computador, para poder realizar a conexão com o banco de dados.

> Ter o Long Path(poder exceder o número máximo de caracteres em um comando) habilitado no Windows, para poder baixar os requirements.

Baixar e instalar o: [Build Tools](https://visualstudio.microsoft.com/pt-br/visual-cpp-build-tools/)

Baixe a versão mais recente do basic package do: [cx_Oracle](https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html)



Utilize o seguinte comando no PowerShell como Administrador para permitir que o Windows utilize o Long Path:

```
"New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
-Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force"
```




Após isso extraia e copie o diretorio da pasta, substituindo na linha 12 codigo o caminho.
```
lib_dir = r"D:\oracle\instantclient_21_12"  (substitua para seu caminho)
```



Após clonar o repositorio utilize os seguintes comandos, para reinstalar o Python e utilizar diretamente o do seu computador:

```
python -m pip install --upgrade --force-reinstall pip // python -m pip install --upgrade --force-reinstall pip
```

Para evitar problemas de instalação limpe o cache:
```
python -m pip cache purge
```

Crie o ambiente virtual (venv) e ative ele com os comandos:
```
python -m venv venv
venv\Scripts\activate
```


para baixar os packages necessarios:

```
pip install -r  requirements.txt 
```

para rodar a aplicação:

```
python -m streamlit run teste.py
```




