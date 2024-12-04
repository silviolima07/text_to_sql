# https://discuss.streamlit.io/t/the-sqlite3-version-3-34-1-on-streamlit-cloud-is-too-old-could-you-upgrade-it/48019
#import pysqlite3
import sys 
#sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import pandas as pd
import streamlit as st
from crewai import Crew, Process

import os
import sys
import argparse
import logging
from typing import Optional
import pandas as pd
import openai
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
import os
import time
from openai import OpenAI


flag = True
# Verifica se as chaves estão acessíveis
assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY não está configurada!"
assert os.getenv("GROQ_API_KEY"), "GROQ_API_KEY não está configurada!"
assert os.getenv("SERPER_API_KEY"), "SERPER_API_KEY não está configurada!"

from PIL import Image
#import litellm  # Importando o LiteLLM para usar o Groq
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message="Overriding of current TracerProvider is not allowed")


    
def carregar_tabela( ):
    """
    Lê o arquivo CSV.

    Args:
        caminho_arquivo (str): Caminho para o arquivo.

    Returns:
        dataframe: tabela.
    """
    #st.write("Carregar tabela")
    try:
        # Ler o arquivo Excel para obter o esquema do banco de dados
        csv_file = st.file_uploader('Choose a file', type= ['csv'] )
        
        if csv_file is not None:
            data = pd.read_csv(csv_file, sep=';', encoding='ISO-8859-1')
            st.success("Arquivo carregado com sucesso!")
            return data
        else:
            st.warning("Por favor, carregue um arquivo CSV.")  
            return None            
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")
        st.error(f"Erro ao carregar o arquivo CSV: {e}")
        raise

def texto_para_sql(consulta_linguagem_natural: str, esquema: str, modelo: str) -> Optional[str]:
    """
    Converte a consulta em linguagem natural em uma consulta SQL usando a API da OpenAI.

    Args:
        consulta_linguagem_natural (str): Consulta em linguagem natural.
        esquema (str): Esquema da tabela.
        modelo (str): Modelo da OpenAI a ser utilizado.

    Returns:
        Optional[str]: A consulta SQL gerada ou None em caso de falha.
    """
    # Ajustar entrada para o modelo
    

    try:
        api_key=os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            st.error("Chave da API OpenAI não encontrada. Verifique as variáveis de ambiente.")
            return None

        # Configurar o cliente OpenAI
        openai.api_key = api_key
        client = OpenAI()
        
        
        # # Fazer a chamada à API da OpenAI
        with st.spinner("Gerando consulta SQL..."):
            time.sleep(5)
            resposta = client.chat.completions.create(
             model=modelo,
            messages=[
                 {"role": "system", "content": "Você é um assistente que converte linguagem natural em consultas SQL."},
                 {"role": "user", "content": f"{esquema}\n\nGere uma consulta SQL para a seguinte solicitação:\nSolicitação: {consulta_linguagem_natural}\nConsulta SQL:"}
             ],
             temperature=0
         )
        st.write("Consulta convertida para SQL pelo modelo")
        resposta_dict = resposta.model_dump() # convert to dict
        consulta_sql = resposta_dict["choices"][0]["message"]["content"].strip()
        return consulta_sql
        
    except openai.RateLimitError:
        st.error("Taxa de limite excedida ao chamar a API da OpenAI. Tente novamente mais tarde.")
    except openai.APIConnectionError:
        st.error("Erro de conexão com a API da OpenAI.")
    except openai.AuthenticationError:
        st.error("Erro de autenticação com a API da OpenAI. Verifique sua chave de API.")
    except openai.InvalidRequestError as e:
        st.error(f"Erro de solicitação inválida à API da OpenAI: {e}")
    except openai.OpenAIError as e:
         st.error(f"Erro ao chamar a API da OpenAI: {e}")
    return None

import re

def filtrar_comandos_sql(texto: str) -> str:
    """
    Filtra os comandos SQL de um texto.

    Args:
        texto (str): O texto de entrada contendo a consulta SQL.

    Returns:
        str: O comando SQL filtrado ou uma string vazia se não encontrado.
    """
    # Procurar o trecho SQL usando delimitadores conhecidos
    padrao = r"```sql(.*?)```"
    match = re.search(padrao, texto, re.DOTALL)  # DOTALL permite que "." capture múltiplas linhas

    if match:
        comando_sql = match.group(1).strip()  # Extrair e limpar espaços
        return comando_sql
    else:
        return None

def parse_arguments():
    """
    Analisa os argumentos da linha de comando.

    Returns:
        Namespace: Argumentos analisados.
    """
    parser = argparse.ArgumentParser(description='Converte consultas em linguagem natural em SQL.')
    parser.add_argument('--arquivo', type=str, default='dados-precos.xlsx', help='Caminho para o arquivo Excel com os dados.')
    parser.add_argument('--modelo', type=str, default='gpt-4o-mini', help='Modelo da OpenAI a ser usado.')
    return parser.parse_args()



def input_user():
    """
    Obtém a entrada do usuário e valida que não está vazia.

    Returns:
        str: Consulta em linguagem natural.
    """
    #st.write("Input user")
    while True:
        consulta_nl = st.text_input("Digite sua consulta em linguagem natural: ")
        if consulta_nl.strip():
            return consulta_nl  # Retorna a entrada válida
        else:
            st.error("Aguardando incluir a consulta")
            return None
            
    
    
# Inicio da lógica do app

img0 = Image.open("img/robo.png")
st.sidebar.image(img0, caption="", use_container_width=True)

html_page_title = """
     <div style="background-color:black;padding=60px">
         <p style='text-align:center;font-size:50px;font-weight:bold'>Text to SQL</p>
     </div>
     """
st.markdown(html_page_title, unsafe_allow_html=True)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Analisar argumentos
args = parse_arguments()

# Carregar o esquema da tabela
try:
    data = carregar_tabela()
    if data is not None:
        st.write("Dataset:",data.shape)
        # Extrair as colunas do arquivo Excel
        st.dataframe(data.head(3))
        colunas = data.columns.tolist()
        # Criar esquema explícito da tabela com nomes em português
        st.markdown("#### A tabela tem as seguintes colunas:")
        esquema = f"A tabela 'dados' tem as seguintes colunas: {', '.join(colunas)}."
        for col in colunas:
            st.write('-',col)
            
        # Obter a entrada do usuário
        consulta_nl = input_user()
        
        if consulta_nl is not None:
            st.markdown("### 🙄 Consulta:")
            st.markdown("##### " + consulta_nl)
        
            if st.button(" ⚙️ ▶️ Enviar"):    

                # Obter a consulta SQL
                consulta_sql = texto_para_sql(consulta_nl, esquema, args.modelo)
                if consulta_sql is not None:
                    #st.success("Consulta SQL gerada")
                    # Exibir a consulta gerada
                    try:
                        consulta_sql = filtrar_comandos_sql(consulta_sql)
                        if consulta_sql is not None:
                            st.success("Consulta SQL gerada com sucesso!")
                            st.code(consulta_sql, language='sql')

                            nome_arquivo = "SQL/consulta_sql.txt"
                            caminho_arquivo = os.path.join(os.getcwd(), nome_arquivo)
                            with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
                                arquivo.write(consulta_sql)
                                st.success(f"Consulta SQL salva.")    
                                st.write(f"Arquivo '{caminho_arquivo}'")
                               
                    except Exception as e:
                        st.error(f"Erro ao converter a consulta em SQL: {e}")
                        sys.exit(1)

            
except Exception as e:
        st.error(f"Erro ao carregar o esquema da tabela: {e}")
        sys.exit(1)
        
        
