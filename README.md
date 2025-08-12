# sefaz-nfe-status

Consulta de status de NF-e utilizando o serviço **NFeConsultaProtocolo4** da SEFAZ, com autenticação via **certificado digital A1** no formato PEM.

---

## 📖 Visão Geral

Este projeto tem como objetivo demonstrar a integração com o Web Service da SEFAZ para obter o status atual de uma Nota Fiscal eletrônica (NF-e) a partir de sua **chave de acesso**.

O repositório inclui:

- Estrutura de diretórios pronta para uso
- Arquivos de configuração `.env` e `.pem` como placeholders
- Script de consulta com saída em **XML** e **JSON**
- Suporte a parâmetros via **.env** ou **CLI**

> **Finalidade**: estudo, prototipagem e integração com sistemas fiscais.  
> **Atenção**: os certificados e chaves incluídos são apenas placeholders, sem dados válidos.

---

## 📂 Estrutura do Projeto

sefaz-nfe-status/
├─ src/
│ └─ main_status.py # Script principal
├─ tmp/
│ ├─ cert.pem # Certificado digital A1 (placeholder)
│ └─ key.pem # Chave privada (placeholder)
├─ xml_respostas/ # Saída das consultas
├─ .env # Configurações do projeto
├─ requirements.txt # Dependências
└─ README.md

---

## ⚙ Requisitos

- **Python** 3.10 ou superior
- Certificado Digital A1 (.pem)
- Dependências listadas no `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## 🔧 Configuração

O arquivo `.env` define os parâmetros de execução:

```env
KEY_PATH=tmp/key.pem
CERT_PATH=tmp/cert.pem
XML_ENTRADA=entrada.xml
PASTA_SAIDA=xml_respostas
CHAVE_ACESSO=
UF=35
TP_AMB=1
SSL_VERIFY=false
HTTP_TIMEOUT=30
ENDPOINT=https://nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx
```

**Campos principais:**

- `CHAVE_ACESSO`: chave da NF-e (44 dígitos). Pode ser informada no `.env` ou via argumento de linha de comando.
- `UF`: código IBGE da unidade federativa (35 = SP).
- `TP_AMB`: ambiente (1 = Produção, 2 = Homologação).
- `SSL_VERIFY`: validação de SSL (true/false).
- `HTTP_TIMEOUT`: tempo limite de requisição em segundos.
- `ENDPOINT`: URL do Web Service.

Os arquivos `cert.pem` e `key.pem` fornecidos são placeholders e devem ser substituídos por arquivos reais para uso prático.

---

## ▶ Execução

### 1. Usando parâmetros do `.env`

```bash
python src/main_status.py
```

### 2. Informando chave diretamente via CLI

```bash
python src/main_status.py --chave 3525XXXXXXXXXXXXXX --tp-amb 1 --uf 35
```

---

## 📤 Saída

Após a execução, serão gerados:

- **XML bruto** da resposta da SEFAZ:  
  `xml_respostas/resposta_<CHAVE>.xml`
- **JSON parseado** com os principais campos da consulta:  
  `xml_respostas/parsed_status_<CHAVE>.json`

Exemplo de JSON:

```json
{
  "cStat": "100",
  "xMotivo": "Autorizado o uso da NF-e",
  "nProt": "135230000000000",
  "dhRecbto": "2025-08-10T14:22:35-03:00"
}
```

---

## 📋 Parâmetros de Linha de Comando

| Parâmetro    | Descrição                           | Padrão (.env) |
| ------------ | ----------------------------------- | ------------- |
| `--chave`    | Chave da NF-e (44 dígitos)          | CHAVE_ACESSO  |
| `--uf`       | Código IBGE da UF                   | UF            |
| `--tp-amb`   | Ambiente: 1=Produção, 2=Homologação | TP_AMB        |
| `--endpoint` | URL do Web Service                  | ENDPOINT      |
| `--cert`     | Caminho do certificado PEM          | CERT_PATH     |
| `--key`      | Caminho da chave privada PEM        | KEY_PATH      |
| `--verify`   | Verificar SSL (true/false)          | SSL_VERIFY    |
| `--timeout`  | Tempo limite em segundos            | HTTP_TIMEOUT  |

---

## 📌 Observações

- Este repositório é destinado a fins de estudo e demonstração técnica.
- Certificados e chaves reais devem ser armazenados em local seguro e **nunca** versionados publicamente.
- Antes de usar em produção, confirme o ambiente e o endpoint corretos.

---

## 📜 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
