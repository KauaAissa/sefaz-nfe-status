import os
import re
import json
import argparse
import requests
from lxml import etree

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Defaults via .env (com valores seguros)
DEFAULT_KEY_PATH = os.getenv("KEY_PATH", "tmp/key.pem")
DEFAULT_CERT_PATH = os.getenv("CERT_PATH", "tmp/cert.pem")
DEFAULT_XML_ENTRADA = os.getenv("XML_ENTRADA", "entrada.xml")
DEFAULT_PASTA_SAIDA = os.getenv("PASTA_SAIDA", "xml_respostas")
DEFAULT_CHAVE = os.getenv("CHAVE_ACESSO", "")
DEFAULT_UF = os.getenv("UF", "35")          # 35=SP
DEFAULT_AMBIENTE = os.getenv("TP_AMB", "1")  # 1=Prod, 2=Homolog
DEFAULT_VERIFY = os.getenv("SSL_VERIFY", "false").lower() in ("1","true","yes")
DEFAULT_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "30"))
DEFAULT_ENDPOINT = os.getenv(
    "ENDPOINT",
    "https://nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx"
)

os.makedirs(DEFAULT_PASTA_SAIDA, exist_ok=True)

def valida_chave(chave: str) -> str:
    chave = re.sub(r"\D", "", chave or "")
    if len(chave) != 44:
        raise ValueError("A chave de acesso deve conter exatamente 44 dígitos.")
    return chave

def montar_xml_consulta(chave: str, tp_amb: str):
    ns = "http://www.portalfiscal.inf.br/nfe"
    cons = etree.Element(f"{{{ns}}}consSitNFe", nsmap={None: ns}, versao="4.00")
    etree.SubElement(cons, f"{{{ns}}}tpAmb").text = tp_amb
    etree.SubElement(cons, f"{{{ns}}}xServ").text = "CONSULTAR"
    etree.SubElement(cons, f"{{{ns}}}chNFe").text = chave
    return cons

def salvar_xml(xml_element, caminho):
    tree = etree.ElementTree(xml_element)
    with open(caminho, "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True, pretty_print=True)
    print(f"📁 XML salvo em: {caminho}")

def envelope_soap(xml_str: str, uf: str, versao: str = "4.00") -> str:
    return f"""
    <soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"
                     xmlns:nfe="http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4">
        <soap12:Header>
            <nfe:nfeCabecMsg>
                <nfe:cUF>{uf}</nfe:cUF>
                <nfe:versaoDados>{versao}</nfe:versaoDados>
            </nfe:nfeCabecMsg>
        </soap12:Header>
        <soap12:Body>
            <nfe:nfeDadosMsg>
                {xml_str}
            </nfe:nfeDadosMsg>
        </soap12:Body>
    </soap12:Envelope>
    """.strip()

def enviar(endpoint, xml_enveloped, cert_path, key_path, verify, timeout):
    headers = {"Content-Type": "application/soap+xml; charset=utf-8"}
    resp = requests.post(
        endpoint,
        data=xml_enveloped.encode("utf-8"),
        headers=headers,
        cert=(cert_path, key_path),
        verify=verify,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.text

def extrair_status(resposta_xml: str):
    ns = {
        "soap12": "http://www.w3.org/2003/05/soap-envelope",
        "nfe": "http://www.portalfiscal.inf.br/nfe",
    }
    root = etree.fromstring(resposta_xml.encode("utf-8"))

    def find_text(xpath):
        el = root.find(xpath, namespaces=ns)
        return el.text.strip() if el is not None and el.text else None

    dados = {
        "cStat": find_text(".//nfe:cStat"),
        "xMotivo": find_text(".//nfe:xMotivo"),
        "nProt": find_text(".//nfe:nProt"),
        "dhRecbto": find_text(".//nfe:dhRecbto"),
    }
    return {k: v for k, v in dados.items() if v is not None}

def salvar_resposta(bruta: str, saida_dir: str, chave: str):
    path_xml = os.path.join(saida_dir, f"resposta_{chave}.xml")
    with open(path_xml, "w", encoding="utf-8") as f:
        f.write(bruta)
    print(f"💾 Resposta salva em: {path_xml}")
    return path_xml

def salvar_status(dados: dict, saida_dir: str, chave: str):
    path_json = os.path.join(saida_dir, f"parsed_status_{chave}.json")
    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"📝 Status parseado salvo em: {path_json}")
    return path_json

def parse_args():
    p = argparse.ArgumentParser(description="Consulta status/protocolo da NF-e (NFeConsultaProtocolo4)")
    p.add_argument("--chave", help="Chave de acesso (44 dígitos). Se omitido, usa CHAVE_ACESSO do .env.")
    p.add_argument("--uf", default=DEFAULT_UF, help="Código UF IBGE (ex: 35=SP).")
    p.add_argument("--tp-amb", default=DEFAULT_AMBIENTE, choices=["1", "2"], help="Ambiente: 1=Produção, 2=Homolog.")
    p.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="URL do serviço SOAP.")
    p.add_argument("--cert", default=DEFAULT_CERT_PATH, help="Caminho do cert.pem.")
    p.add_argument("--key", default=DEFAULT_KEY_PATH, help="Caminho do key.pem.")
    p.add_argument("--entrada-xml", default=DEFAULT_XML_ENTRADA, help="Arquivo para salvar o XML de entrada.")
    p.add_argument("--saida", default=DEFAULT_PASTA_SAIDA, help="Pasta de saída.")
    p.add_argument("--verify", default=str(DEFAULT_VERIFY), help="Verificar SSL (true/false).")
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Timeout HTTP em segundos.")
    return p.parse_args()

def main():
    args = parse_args()
    verify = str(args.verify).lower() in ("1","true","yes")
    os.makedirs(args.saida, exist_ok=True)

    # 1) Chave
    chave = args.chave or DEFAULT_CHAVE
    try:
        chave = valida_chave(chave)
    except ValueError as e:
        print(f"❌ {e}")
        return

    # 2) XML de consulta
    xml_el = montar_xml_consulta(chave, args.tp_amb)
    salvar_xml(xml_el, args.entrada_xml)

    xml_str = etree.tostring(xml_el, encoding="utf-8", xml_declaration=False, pretty_print=False).decode("utf-8")
    xml_str = re.sub(r"\s+", " ", xml_str).strip()

    # 3) Envelope SOAP
    envelope = envelope_soap(xml_str, uf=args.uf)
    print("\n📤 XML ENVIADO (SOAP):")
    print(envelope)

    # 4) Envio
    try:
        print("\n📨 Enviando para a SEFAZ...")
        resposta = enviar(
            endpoint=args.endpoint,
            xml_enveloped=envelope,
            cert_path=args.cert,
            key_path=args.key,
            verify=verify,
            timeout=args.timeout,
        )
    except requests.exceptions.SSLError as e:
        print(f"❌ Erro SSL: {e}")
        return
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP {e.response.status_code}: {e.response.text[:400]}")
        return
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de requisição: {e}")
        return

    print("\n📩 Resposta da SEFAZ (bruta):")
    print(resposta[:2000] + ("...\n[truncado]" if len(resposta) > 2000 else ""))

    # 5) Persistência e parse
    salvar_resposta(resposta, args.saida, chave)
    parsed = extrair_status(resposta)
    if parsed:
        salvar_status(parsed, args.saida, chave)
    else:
        print("⚠️ Não foi possível extrair campos de status do XML de resposta.")

if __name__ == "__main__":
    main()
