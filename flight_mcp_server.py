# flight_mcp_server.py
"""
MCP server that exposes a tool to search for the cheapest flights
using the Amadeus Flight Offers Search API.
"""

import os
import sys
import json
import base64
from datetime import datetime
from typing import Optional, List, Dict, Any

import httpx
from mcp.server.fastmcp import FastMCP

# -------------------------------------------------
# Amadeus OAuth2 token handling
# -------------------------------------------------
AMADEUS_TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_OFFERS_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

def _get_amadeus_token() -> str:
    """Fetch an OAuth2 client‑credentials token from Amadeus."""
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Missing Amadeus credentials. Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET env vars."
        )

    # Encode client_id:client_secret for Basic Auth
    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}

    with httpx.Client() as client:
        resp = client.post(AMADEUS_TOKEN_URL, headers=headers, data=data)
        resp.raise_for_status()
        token_data = resp.json()
        return token_data["access_token"]


# -------------------------------------------------
# Helper to format Amadeus response
# -------------------------------------------------
def _format_flight_offer(offer: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a compact, readable representation from a raw Amadeus offer."""
    # Basic price information
    price = offer.get("price", {})
    total_price = price.get("total")
    currency = price.get("currency")

    # Itineraries (outbound & inbound if round‑trip)
    itineraries = offer.get("itineraries", [])
    formatted_legs: List[Dict[str, Any]] = []

    for idx, itinerary in enumerate(itineraries):
        segments = itinerary.get("segments", [])
        leg_info = {
            "direction": "outbound" if idx == 0 else "inbound",
            "stops": len(segments) - 1,
            "duration": itinerary.get("duration"),
            "segments": [],
        }
        for seg in segments:
            carrier_code = seg.get("carrierCode")
            flight_number = seg.get("number")
            dep = seg.get("departure")
            arr = seg.get("arrival")
            leg_info["segments"].append(
                {
                    "carrier": carrier_code,
                    "flight_number": flight_number,
                    "departure_at": dep.get("at") if dep else None,
                    "departure_iata": dep.get("iataCode") if dep else None,
                    "arrival_at": arr.get("at") if arr else None,
                    "arrival_iata": arr.get("iataCode") if arr else None,
                }
            )
        formatted_legs.append(leg_info)

    return {
        "price": f"{total_price} {currency}" if total_price and currency else None,
        "itineraries": formatted_legs,
        "number_of_bookable_seats": offer.get("numberOfBookableSeats"),
    }


# -------------------------------------------------
# FastMCP server definition
# -------------------------------------------------
mcp = FastMCP("Chasseur de Vols")


@mcp.tool()
def rechercher_vols_economiques(
    origine: str,
    destination: str,
    date_depart: str,
    date_retour: Optional[str] = None,
) -> str:
    """
    Recherche les vols les moins chers entre deux aéroports.

    Args:
        origine: Code IATA de l'aéroport d'origine (ex: "PAR").
        destination: Code IATA de l'aéroport de destination (ex: "TYO").
        date_depart: Date de départ au format YYYY-MM-DD.
        date_retour: (Optionnel) Date de retour au format YYYY-MM-DD pour un aller‑retour.

    Returns:
        Une chaîne JSON contenant une liste d'offres de vols triées par prix croissant.
        Chaque offre contient : prix, nombre d'escales, durée, détails des segments.
    """
    try:
        token = _get_amadeus_token()
    except Exception as exc:
        return json.dumps({"error": f"Échec d'authentification Amadeus : {exc}"}, ensure_ascii=False)

    # Build request parameters
    params: Dict[str, Any] = {
        "originLocationCode": origine.upper(),
        "destinationLocationCode": destination.upper(),
        "departureDate": date_depart,
        "adults": 1,
        "max": 10,  # limit to keep response small
    }
    if date_retour:
        params["returnDate"] = date_retour

    headers = {"Authorization": f"Bearer {token}"}

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(AMADEUS_OFFERS_URL, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as http_err:
        return json.dumps(
            {"error": f"Erreur HTTP Amadeus ({http_err.response.status_code}) : {http_err.response.text}"},
            ensure_ascii=False,
        )
    except Exception as exc:
        return json.dumps({"error": f"Erreur lors de l'appel Amadeus : {exc}"}, ensure_ascii=False)

    offers = data.get("data", [])
    if not offers:
        return json.dumps(
            {"message": "Aucun vol trouvé pour les critères spécifiés."},
            ensure_ascii=False,
        )

    # Sort by price (cheapest first)
    def _price_key(offer):
        try:
            return float(offer["price"]["total"])
        except Exception:
            return float("inf")

    sorted_offers = sorted(offers, key=_price_key)

    # Format each offer for compactness
    formatted = [_format_flight_offer(o) for o in sorted_offers]

    return json.dumps({"results": formatted}, ensure_ascii=False, indent=2)


# -------------------------------------------------
# Entrypoint
# -------------------------------------------------
if __name__ == "__main__":
    # Run the MCP server over stdio (the default for Claude Desktop)
    mcp.run()