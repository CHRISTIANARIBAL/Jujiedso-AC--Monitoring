import asyncio
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .config import OLTS
from .services import run_vsol, run_bdcom


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

@csrf_exempt
@require_POST
def lookup(request):
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
    mac = data.get("mac")

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

    if not mac:
        return JsonResponse({
            "success": False,
            "error": "MAC address is required."
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

    # username = olt["username"]
    # password = olt["password"]

    try:
        if olt["brand"] == "VSOL":
            result = asyncio.run(
                run_vsol(
                    olt_name,
                    olt,
                    username,
                    password,
                    mac
                )
            )

        elif olt["brand"] == "BDCOM":
            result = asyncio.run(
                run_bdcom(
                    olt_name,
                    olt,
                    username,
                    password,
                    mac
                )
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