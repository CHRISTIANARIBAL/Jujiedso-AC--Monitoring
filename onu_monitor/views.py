import asyncio
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from .config import OLTS
from .services import run_vsol, run_bdcom
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def index(request):
    return render(request, "onu_monitor/index.html")


@require_GET
def get_olts(request):
    result = {}

    for name, olt in OLTS.items():
        result[name] = {
            "brand": olt["brand"],
            "ip": olt["ip"],
        }

    return JsonResponse(result)

@require_POST
async def lookup(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON request."
        }, status=400)

    olt_name = data.get("olt")
    username = data.get("username")
    password = data.get("password")
    lookup_mode = data.get("mode", "mac")
    value = data.get("value")

    if not olt_name:
        return JsonResponse({
            "success": False,
            "error": "OLT was not selected."
        }, status=400)

    if olt_name not in OLTS:
        return JsonResponse({
            "success": False,
            "error": "Invalid OLT."
        }, status=400)

    if lookup_mode not in ["mac", "onu"]:
        return JsonResponse({
            "success": False,
            "error": "Invalid lookup mode."
        }, status=400)

    if not value:
        return JsonResponse({
            "success": False,
            "error": "Lookup value is required."
        }, status=400)

    if not username:
        return JsonResponse({
            "success": False,
            "error": "Username is required."
        }, status=400)

    if not password:
        return JsonResponse({
            "success": False,
            "error": "Password is required."
        }, status=400)

    olt = OLTS[olt_name]

    try:

        if olt["brand"] == "VSOL":
            result = await run_vsol(
                olt_name,
                olt,
                username,
                password,
                value,
                lookup_mode
            )

        elif olt["brand"] == "BDCOM":
            result = await run_bdcom(
                olt_name,
                olt,
                username,
                password,
                value,
                lookup_mode
            )

        else:
            return JsonResponse({
                "success": False,
                "error": "Unsupported OLT brand."
            }, status=400)

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)
