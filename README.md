# Facebook Lead Converter

![Facebook Lead Converter](https://img.shields.io/badge/Version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)
![Facebook API](https://img.shields.io/badge/Facebook-API-blue)

Uma interface gráfica em Python para converter e enviar leads do Excel para o Facebook Conversions API.

## 👤 Autor

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/ricardochristovao">
        <img src="https://github.com/ricardochristovao.png" width="100px;" alt="Ricardo Christovão"/><br>
        <sub>
          <b>Ricardo Christovão da Silva</b>
        </sub>
      </a>
    </td>
  </tr>
</table>

[![GitHub](https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github)](https://github.com/ricardochristovao)
[![LinkedIn](https://img.shields.io/badge/-LinkedIn-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/ricardochristovao)

---
## 📥 Download
Você pode baixar a versão mais recente do executável na seção [Releases](https://github.com/ricardochristovao/facebook-lead-converter/releases).

---

## 🚀 Funcionalidades

- ✨ Interface gráfica amigável
- 📊 Importação de planilhas Excel/CSV
- 🔄 Mapeamento flexível de colunas
- 🔐 Gerenciamento de credenciais do Facebook
- 📝 Log detalhado de operações
- ⚡ Processamento em thread separada
- 🔍 Exportação automática de registros com falha

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Credenciais do Facebook (Access Token e Pixel ID)
- Planilha com dados dos leads

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/ricardochristovao/facebook-lead-converter.git
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute o programa:
```bash
python main.py
```

## 📦 Estrutura da Planilha

A planilha deve conter as seguintes colunas (o mapeamento pode ser feito na interface):
- nome
- email
- telefone
- utm_source
- utm_medium
- utm_term
- utm_campaign
- utm_content
- data_registro
- ip

## 💻 Como Usar

1. Inicie o programa
2. Configure as credenciais do Facebook (Access Token e Pixel ID)
3. Selecione a planilha com os leads
4. Mapeie as colunas conforme necessário
5. Clique em "Iniciar Processamento"
6. Acompanhe o progresso na interface

## ⚙️ Configuração
O programa salva as credenciais em um arquivo config.json para uso futuro. As credenciais podem ser atualizadas a qualquer momento através da interface.

## 📄 Logs
Os logs são salvos automaticamente em arquivos com o formato:
```bash
facebook_conversion_log_YYYYMMDD_HHMMSS.txt
```

## 🔒 Segurança
- Dados sensíveis são hasheados antes do envio
- Credenciais são armazenadas localmente
- Suporte a HTTPS para comunicação com a API

## 🛠️ Tecnologias Utilizadas
- Python
- tkinter (interface gráfica)
- pandas (manipulação de dados)
- facebook-business-sdk
- threading (processamento assíncrono)

## ⚠️ Tratamento de Erros

- Validação de credenciais
- Verificação de formato de dados
- Exportação automática de falhas
- Logs detalhados de erros

## 📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

---
