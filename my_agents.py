from crewai import Agent
import streamlit as st
import crewai_tools

from crewai_tools import SerperDevTool

from MyLLM import MyLLM

#from config_modelo import selecionar_modelo

from dotenv import load_dotenv
# Carregar variáveis de ambiente
load_dotenv()

import os

# Obter a chave da API GROQ
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Definir o modelo de linguagem

#llm = MyLLM.GROQ_MIXTRAL
llm = MyLLM.GROQ_LLAMA

#st.write("LLM: ", llm.model)

# Initialize the tool for internet searching capabilities
serper_tool = SerperDevTool()
serper_tool.n_results = 10

# Configuração do agente

   
guia_compras = Agent(
        role="Pesquisador",
        goal="Pesquisar e recomendar 3 presentes",
        backstory=
            "Você é especalista em pesquisa de presentes."   
        ,
        llm=llm, # estava provider=provider
        verbose=False,
        memory=False,
        tools=[serper_tool]
    )

    
    
    
