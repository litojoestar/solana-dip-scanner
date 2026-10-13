import os
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Solana DIP Scanner", page_icon="🧩", layout="wide")

DEX = "https://api.dexscreener.com"
PROFILE_URL = f"{DEX}/token-profiles/latest/v1"
BOOST_URL = f"{DEX}/token-boosts/latest/v1"
TOKENS_URL = f"{DEX}/tokens/v1/solana/"

st.title("🧩 Solana DIP Scanner")
st.caption("Scanner éducatif de memecoins — surveillance uniquement, aucun achat automatique.")

with st.sidebar:
    st.header("Filtres")
    min_liq = st.number_input("Liquidité minimale ($)", min_value=0, value=25000, step=5000)
    min_vol = st.number_input("Volume 24 h minimum ($)", min_value=0, value=10000, step=2500)
    dip_min = st.slider("Baisse minimale sur 24 h (%)", min_value=1, max_value=80, value=15)
    dip_max = st.slider("Baisse maximale sur 24 h (%)", min_value=5, max_value=95, value=50)
    only_dips = st.checkbox("Afficher uniquement les baisses", value=True)
    st.caption("Les seuils sont des filtres de départ, pas des recommandations d'achat.")

def get_json(url, timeout=15):
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "SolanaDIPScanner/1.0"})
    r.raise_for_status()
    return r.json()

def safe_num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def check_stabilization(pool_address):
    """Vérifie prudemment les 3 dernières bougies de 5 minutes."""
    if not pool_address:
        return False, "Adresse de pool manquante"

    url = (
        "https://api.geckoterminal.com/api/v2/networks/solana/pools/"
        f"{pool_address}/ohlcv/minute?aggregate=5&limit=6&currency=usd&token=base"
    )

    try:
        response = requests.get(
            url, timeout=10, headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        data = (
            response.json()
            .get("data", {})
            .get("attributes", {})
            .get("ohlcv_list", [])
        )

        if len(data) < 3:
            return False, "Historique de bougies insuffisant"

        candles = list(reversed(data))
        recent = candles[-3:]
        lows = [safe_num(c[3], -1) for c in recent]
        closes = [safe_num(c[4], -1) for c in recent]

        if any(value <= 0 for value in lows + closes):
            return False, "Bougies invalides ou incomplètes"

        stable = lows[-1] >= min(lows[:-1]) and closes[-1] >= closes[-2]

        if stable:
            return True, "Stabilisation provisoire détectée"

        return False, "Pas de stabilisation confirmée"

    except Exception:
        return False, "Historique indisponible — stabilisation non vérifiée"

    url = (
        "https://api.geckoterminal.com/api/v2/networks/solana/pools/"
        f"{pool_address}/ohlcv/minute?aggregate=5&limit=6&currency=usd&token=base"
    )

    try:
        response = requests.get(
            url, timeout=10, headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        data = (
            response.json()
            .get("data", {})
            .get("attributes", {})
            .get("ohlcv_list", [])
        )

        if len(data) < 3:
            return False, "Historique de bougies insuffisant"

        candles = list(reversed(data))
        recent = candles[-3:]
        lows = [safe_num(c[3], -1) for c in recent]
        closes = [safe_num(c[4], -1) for c in recent]

        if any(value <= 0 for value in lows + closes):
            return False, "Bougies invalides ou incomplètes"

        stable = lows[-1] >= min(lows[:-1]) and closes[-1] >= closes[-2]

        if stable:
            return True, "Stabilisation provisoire détectée"

        return False, "Pas de stabilisation confirmée"

    except Exception:
        return False, "Historique indisponible — stabilisation non vérifiée"


def assess_pair_risk(price, liquidity, volume_24h, pair_age_hours):
    """Signale les risques évidents à partir des données de marché."""
    risks = []

    if price is None or safe_num(price, 0) <= 0:
        risks.append("Prix absent ou invalide")

    if liquidity is None or safe_num(liquidity, 0) < 10000:
        risks.append("Liquidité inférieure à 10 000 $")

    if volume_24h is None or safe_num(volume_24h, -1) < 0:
        risks.append("Volume 24 h absent ou invalide")

    if pair_age_hours is None or safe_num(pair_age_hours, -1) < 0:
        risks.append("Âge de paire indisponible")
    elif safe_num(pair_age_hours, 0) < 24:
        risks.append("Paire très récente : moins de 24 h")

    return risks
    
    """Signale les risques évidents à partir des données de marché."""
    risks = []

    if price is None or safe_num(price, 0) <= 0:
        risks.append("Prix absent ou invalide")
    if liquidity is None or safe_num(liquidity, 0) < 10000:
        risks.append("Liquidité inférieure à 10 000 $")
    if volume_24h is None or safe_num(volume_24h, -1) < 0:
        risks.append("Volume 24 h absent ou invalide")
    if pair_age_hours is None or safe_num(pair_age_hours, -1) < 0:
        risks.append("Âge de paire indisponible")
    elif safe_num(pair_age_hours, 0) < 24:
        risks.append("Paire très récente : moins de 24 h")

    return risks
    """Vérifie prudemment les 3 dernières bougies de 5 minutes."""
    if not pool_address:
        return False, "Adresse de pool manquante"

    url = (
        "https://api.geckoterminal.com/api/v2/networks/solana/pools/"
        f"{pool_address}/ohlcv/minute?aggregate=5&limit=6&currency=usd&token=base"
    )
    try:
        response = requests.get(
            url, timeout=10, headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        data = response.json().get("data", {}).get("attributes", {}).get("ohlcv_list", [])

        if len(data) < 3:
            return False, "Historique de bougies insuffisant"

        candles = list(reversed(data))
        recent = candles[-3:]
        lows = [safe_num(c[3], -1) for c in recent]
        closes = [safe_num(c[4], -1) for c in recent]

        if any(value <= 0 for value in lows + closes):
            return False, "Bougies invalides ou incomplètes"

        stable = lows[-1] >= min(lows[:-1]) and closes[-1] >= closes[-2]

        if stable:
            return True, "Stabilisation provisoire détectée"
        return False, "Pas de stabilisation confirmée"

    except Exception:
        return False, "Historique indisponible — stabilisation non vérifiée"
        return float(value or 0)
    except (TypeError, ValueError):
        return default

@st.cache_data(ttl=90, show_spinner=False)
def load_market():
    profiles = get_json(PROFILE_URL)
    boosts = get_json(BOOST_URL)
    items = []
    for source, label in ((profiles, "profile"), (boosts, "boost")):
        if isinstance(source, list):
            for x in source:
                if x.get("chainId") == "solana" and x.get("tokenAddress"):
                    items.append({"address": x["tokenAddress"], "source": label})
    # Preserve first occurrence and keep API usage modest.
    seen, addresses = set(), []
    for item in items:
        if item["address"] not in seen:
            seen.add(item["address"])
            addresses.append(item["address"])
    addresses = addresses[:30]
    if not addresses:
        return []
    pairs = get_json(TOKENS_URL + ",".join(addresses))
    return pairs if isinstance(pairs, list) else []

if st.button("🔄 Actualiser les données", type="primary"):
    load_market.clear()

try:
    with st.spinner("Récupération des données publiques…"):
        pairs = load_market()
except Exception as e:
    st.error("Impossible de récupérer les données de marché pour le moment.")
    st.caption(f"Détail technique : {e}")
    st.info("Réessaie plus tard. L'API publique peut être temporairement indisponible ou limiter les requêtes.")
    st.stop()

rows = []
for p in pairs:
    base = p.get("baseToken") or {}
    price = safe_num(p.get("priceUsd"))
    liq = safe_num((p.get("liquidity") or {}).get("usd"))
    vol = safe_num((p.get("volume") or {}).get("h24"))
    change = safe_num((p.get("priceChange") or {}).get("h24"))
    txns = p.get("txns") or {}
    h1 = txns.get("h1") or {}
    h24 = txns.get("h24") or {}
    buys1, sells1 = int(safe_num(h1.get("buys"))), int(safe_num(h1.get("sells")))
    buys24, sells24 = int(safe_num(h24.get("buys"))), int(safe_num(h24.get("sells")))
    created = p.get("pairCreatedAt")
    age_hours = None
    if created:
        try:
            age_hours = max(0, (datetime.now(timezone.utc).timestamp() * 1000 - float(created)) / 3600000)
        except Exception:
            pass
    # A "watch" signal, not an entry recommendation.
    reasons = []
    if liq >= min_liq: reasons.append("liquidité au-dessus du seuil")
    if vol >= min_vol: reasons.append("volume 24 h suffisant")
    if buys1 > sells1: reasons.append("achats h1 > ventes h1")
    dip_ok = -dip_max <= change <= -dip_min
    if dip_ok: reasons.append("baisse dans la plage choisie")
    risk_notes = []
    if liq < min_liq: risk_notes.append("liquidité faible")
    if vol < min_vol: risk_notes.append("volume faible")
    if sells1 > buys1: risk_notes.append("ventes h1 > achats h1")
    if age_hours is not None and age_hours < 24: risk_notes.append("paire très récente")
    rows.append({
        "Token": base.get("symbol") or base.get("name") or "Unknown",
        "Nom": base.get("name") or "Inconnu",
        "Prix ($)": price,
        "Variation 24 h (%)": change,
        "Liquidité ($)": liq,
        "Volume 24 h ($)": vol,
        "Achats h1": buys1,
        "Ventes h1": sells1,
        "Âge paire (h)": round(age_hours, 1) if age_hours is not None else None,
        "Signal": "À surveiller" if dip_ok and liq >= min_liq and vol >= min_vol and buys1 > sells1 else "Pas de signal complet",
        "Risques / notes": ", ".join(risk_notes) or "Aucun filtre simple déclenché",
        "Graphique": p.get("url") or "",
        "Adresse": base.get("address") or "",
    })

df = pd.DataFrame(rows)
if df.empty:
    st.warning("Aucune paire Solana n'a été renvoyée par les sources actuelles. Réessaie plus tard.")
    st.stop()

filtered = df[(df["Liquidité ($)"] >= min_liq) & (df["Volume 24 h ($)"] >= min_vol)]
if only_dips:filtered = filtered.copy()

for idx, row in filtered.iterrows():
    risks = []
    age = pd.to_numeric(row.get("Âge paire (h)"), errors="coerce")
    price = pd.to_numeric(row.get("Prix ($)"), errors="coerce")
    liquidity = pd.to_numeric(row.get("Liquidité ($)"), errors="coerce")
    volume = pd.to_numeric(row.get("Volume 24 h ($)"), errors="coerce")

    if pd.isna(age):
        risks.append("Âge indisponible")
    elif age < 24:
        risks.append("Paire très récente (<24 h)")

    if pd.isna(price) or price <= 0:
        risks.append("Prix absent ou invalide")
    if pd.isna(liquidity) or liquidity < 10000:
        risks.append("Liquidité faible (<10 000 $)")
    if pd.isna(volume) or volume < 0:
        risks.append("Volume invalide")

    existing = str(row.get("Risques / notes", "")).strip()
    all_risks = [
        r for r in [existing, "; ".join(risks)]
        if r and r.lower() != "nan"
    ]
    filtered.at[idx, "Risques / notes"] = (
        "; ".join(all_risks) if all_risks
        else "Aucun risque détecté par ces contrôles simples"
    )
    filtered = filtered[(filtered["Variation 24 h (%)"] <= -dip_min) & (filtered["Variation 24 h (%)"] >= -dip_max)]

c1, c2, c3 = st.columns(3)
c1.metric("Paires récupérées", len(df))
c2.metric("Paires après filtres", len(filtered))
c3.metric("Signaux à surveiller", int((filtered["Signal"] == "À surveiller").sum()))

st.warning("Un signal signifie seulement que des critères simples sont réunis. Il ne prouve ni un rebond ni la sécurité du token. Les données peuvent être retardées ou incomplètes.")

display_cols = ["Token", "Nom", "Prix ($)", "Variation 24 h (%)", "Liquidité ($)", "Volume 24 h ($)", "Achats h1", "Ventes h1", "Âge paire (h)", "Signal", "Risques / notes", "Graphique"]
st.subheader("Tokens repérés")
if filtered.empty:
    st.info("Aucun token ne correspond à tous les filtres actuellement. Décoche « Afficher uniquement les baisses » ou ajuste les seuils.")
else:
    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Prix ($)": st.column_config.NumberColumn(format="$%.8f"),
            "Variation 24 h (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Liquidité ($)": st.column_config.NumberColumn(format="$%.0f"),
            "Volume 24 h ($)": st.column_config.NumberColumn(format="$%.0f"),
            "Graphique": st.column_config.LinkColumn("Graphique DEX"),
        },
    )

with st.expander("Détails des données brutes"):
st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)

st.subheader("Telegram — configuration facultative")
st.write("Pour activer les alertes, ajoute les secrets `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID` dans les paramètres Secrets de Streamlit. Les alertes sont envoyées uniquement quand tu appuies sur le bouton ci-dessous.")
token = st.secrets.get("TELEGRAM_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN", ""))
chat_id = st.secrets.get("TELEGRAM_CHAT_ID", os.getenv("TELEGRAM_CHAT_ID", ""))
if st.button("📨 Envoyer les signaux actuels sur Telegram"):
    if not token or not chat_id:
        st.error("Telegram n'est pas configuré. Suis le guide README, puis ajoute les secrets dans Streamlit.")
    elif filtered.empty:
        st.info("Aucun résultat filtré à envoyer.")
    else:
        signals = filtered[filtered["Signal"] == "À surveiller"]
        if signals.empty:
            st.info("Aucun signal complet à envoyer pour le moment.")
        else:
            message_lines = ["🧩 Solana DIP Scanner — alertes de surveillance"]
            for _, row in signals.head(10).iterrows():
                message_lines.append(
                    f"• {row['Token']} | variation 24 h: {row['Variation 24 h (%)']:.2f}% | "
                    f"liquidité: ${row['Liquidité ($)']:,.0f} | volume: ${row['Volume 24 h ($)']:,.0f}\n"
                    f"{row['Graphique']}"
                )
            message = "\n\n".join(message_lines)
            try:
                resp = requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": message, "disable_web_page_preview": True},
                    timeout=15,
                )
                resp.raise_for_status()
                if resp.json().get("ok"):
                    st.success("Alerte envoyée sur Telegram.")
                else:
                    st.error("Telegram n'a pas confirmé l'envoi. Vérifie le token et le chat ID.")
            except Exception as e:
                st.error(f"Échec d'envoi Telegram : {e}")

st.caption("Sources de marché : API publique DEX Screener. Le scanner utilise les profils et tokens boostés récents, il ne couvre donc pas tous les tokens Solana.")
