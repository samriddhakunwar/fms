from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .decorators import role_required


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return _redirect_by_role(user)
        else:
            error = "Invalid username or password."

    return render(request, "login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@role_required("ADMIN")
def admin_dashboard(request):
    return render(request, "admin_dashboard.html")


@role_required("INVENTORY_MANAGER")
def inventory_dashboard(request):
    return render(request, "inventory_dashboard.html")


@role_required("EMPLOYEE")
def employee_dashboard(request):
    return render(request, "employee_dashboard.html")


def _redirect_by_role(user):
    role = user.role
    if role == "ADMIN":
        return redirect("accounts:admin_dashboard")
    elif role == "INVENTORY_MANAGER":
        return redirect("accounts:inventory_dashboard")
    elif role == "EMPLOYEE":
        return redirect("accounts:employee_dashboard")
    else:
        return redirect("accounts:login")
