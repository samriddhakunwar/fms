from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum

from fms.dates import day_range_filter

PASSWORD = "FMS@1234"  # same password for every seed user

# username, first_name, last_name, role, phone (email is <first_name>@fms.local)
USERS = [
    ("alice_admin", "Alice", "Rahman", "ADMIN", "01711-000001"),
    ("bob_inv", "Bob", "Hossain", "MANAGER", "01711-000002"),
    ("carol_inv", "Carol", "Akter", "MANAGER", "01711-000003"),
    ("dan_emp", "Dan", "Miah", "STAFF", "01711-000004"),
    ("eva_emp", "Eva", "Begum", "STAFF", "01711-000005"),
]

# sku, name, description, price, stock, minimum
PRODUCTS = [
    ("PRD-001", "Industrial Bolt Set (M12)", "High-tensile steel bolts used in heavy machinery assemblies.", "1250.00", 500, 50),
    ("PRD-002", "Bearing Unit 6205", "Deep-groove ball bearing for conveyor belt rollers.", "875.50", 200, 30),
    ("PRD-003", "Hydraulic Seal Kit", "Replacement seal kit for hydraulic press cylinders.", "3400.00", 80, 10),
    ("PRD-004", "Safety Gloves (Leather)", "Heat-resistant leather gloves for welding and cutting tasks.", "320.00", 15, 20),
    ("PRD-005", "Welding Electrode E6013", "General-purpose mild-steel welding electrode, 3.2 mm diameter.", "540.00", 1000, 100),
]

# full_name, email, phone, address, designation, joining_date, salary, active,
# login username, manager username. Everyone was added by alice_admin.
STAFF = [
    ("Md. Rafiqul Islam", "rafiq@fms.local", "01811-100001", "12, Mirpur Road, Dhaka", "Machine Operator", "2022-03-15", "28000.00", True, "dan_emp", "bob_inv"),
    ("Nasrin Khanam", "nasrin@fms.local", "01811-100002", "45, Gulshan Avenue, Dhaka", "Quality Inspector", "2021-07-01", "32000.00", True, "eva_emp", "bob_inv"),
    ("Karim Bepari", "karim@fms.local", "01811-100003", "7, BSCIC Industrial Area, Chittagong", "Warehouse Supervisor", "2020-01-10", "38000.00", True, None, "bob_inv"),
    ("Ritu Rani Das", "ritu@fms.local", "01811-100004", "33, Tejgaon, Dhaka", "Production Technician", "2023-05-20", "25000.00", True, None, "carol_inv"),
    ("Sohel Mahmud", "sohel@fms.local", "01811-100005", "22, Narayanganj Industrial Zone", "Maintenance Engineer", "2019-11-03", "45000.00", False, None, "carol_inv"),
]


def utc(*args):
    return datetime(*args, tzinfo=dt_timezone.utc)


# order_number, customer, product index, quantity, status, order_date.
# Bob (Manager) took the first three orders, Alice (Admin) the rest.
ORDERS = [
    ("ORD-2026-0001", "Shyam Pvt. Ltd.", 0, 20, "PENDING", utc(2026, 8, 1, 9)),
    ("ORD-2026-0002", "Himalaya Trading Concern", 1, 12, "CONFIRMED", utc(2026, 8, 4, 11)),
    ("ORD-2026-0003", "Sita Hardware Suppliers", 2, 4, "PENDING", utc(2026, 8, 9, 14)),
    ("ORD-2026-0004", "Gorkha Construction Pvt. Ltd.", 4, 60, "CONFIRMED", utc(2026, 8, 14, 10)),
    ("ORD-2026-0005", "Annapurna Steel Udhyog", 3, 10, "CANCELLED", utc(2026, 8, 20, 16)),
]

# invoice_number, sold_to, product index, quantity, unit_price, sale_date
SALES = [
    ("INV-2026-0001", "Shyam Pvt. Ltd.", 0, 10, "1250.00", utc(2026, 7, 10, 9)),
    ("INV-2026-0002", "Himalaya Trading Concern", 1, 5, "875.50", utc(2026, 7, 15, 11)),
    ("INV-2026-0003", "Sita Hardware Suppliers", 2, 3, "3400.00", utc(2026, 7, 20, 14)),
    ("INV-2026-0004", "Gorkha Construction Pvt. Ltd.", 4, 50, "540.00", utc(2026, 7, 25, 10)),
    ("INV-2026-0005", "Annapurna Steel Udhyog", 0, 8, "1300.00", utc(2026, 7, 30, 16)),
]

# username, action, target
ACTIVITY = [
    ("alice_admin", "LOGIN", ""),
    ("bob_inv", "LOGIN", ""),
    ("bob_inv", "VIEW", "staff"),
    ("bob_inv", "VIEW", "sale"),
    ("dan_emp", "LOGIN_FAILED", ""),
    ("dan_emp", "LOGIN", ""),
    ("dan_emp", "VIEW", "product"),
    ("dan_emp", "VIEW", "staff"),
    ("dan_emp", "LOGOUT", ""),
    ("bob_inv", "LOGOUT", ""),
]


def ok(label):
    print(f"  ✅  {label}")


def skip(label):
    print(f"  ⏭   {label} (already exists)")


class Command(BaseCommand):
    help = (
        "Seed mock records for every FMS model (accounts, inventory, employees, "
        "orders, sales, reports, activity log)."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n🌱  Seeding FMS mock data …\n"))
        users = self._seed_users()
        admin, manager = users["alice_admin"], users["bob_inv"]
        products = self._seed_products(admin)
        self._seed_staff(users)
        self._seed_orders(products, admin, manager)
        self._seed_sales(products, admin)
        self._seed_reports(admin, manager)
        self._seed_activity(users)
        self.stdout.write(self.style.SUCCESS("\n✔  Seeding complete.\n"))

    def heading(self, text):
        self.stdout.write(self.style.HTTP_INFO(text))

    def _seed_users(self):
        from accounts.models import ManagerProfile, User

        self.heading("── accounts.User ──────────────────────────")
        users = {}
        for username, first, last, role, phone in USERS:
            user = User.objects.filter(username=username).first()
            if user:
                skip(f"User: {username}")
            else:
                user = User.objects.create(
                    username=username,
                    password=make_password(PASSWORD),
                    first_name=first,
                    last_name=last,
                    email=f"{first.lower()}@fms.local",
                    role=role,
                    phone_number=phone,
                    is_staff=role == User.Role.ADMIN,
                )
                ok(f"User: {username}  ({user.get_role_display()})")
            users[username] = user

        # Managers were created by the seeded Admin.
        ManagerProfile.objects.filter(
            user__in=users.values(), created_by_admin__isnull=True
        ).update(created_by_admin=users["alice_admin"].admin_profile)
        return users

    def _seed_products(self, admin):
        from inventory.models import Product, StockMovement

        self.heading("\n── inventory.Product ───────────────────────")
        products = []
        for sku, name, description, price, stock, minimum in PRODUCTS:
            product, created = Product.objects.get_or_create(
                sku=sku,
                defaults=dict(
                    product_name=name,
                    description=description,
                    selling_price=Decimal(price),
                    quantity_in_stock=stock,
                    minimum_stock_level=minimum,
                    created_by_admin=admin.admin_profile,
                ),
            )
            if created:
                StockMovement.record(
                    product, stock, StockMovement.MovementType.STOCK_IN, admin, "Opening stock"
                )
                ok(f"Product: {name}  (SKU: {sku})")
            else:
                if product.created_by_admin_id is None and product.created_by_manager_id is None:
                    product.created_by_admin = admin.admin_profile
                    product.save(update_fields=["created_by_admin"])
                skip(f"Product SKU {sku}")
            products.append(product)
        return products

    def _seed_staff(self, users):
        from employees.models import Staff

        self.heading("\n── employees.Staff ─────────────────────────")
        for (full_name, email, phone, address, designation, joined, salary,
             active, login, manager) in STAFF:
            data = dict(
                full_name=full_name,
                email=email,
                phone=phone,
                address=address,
                designation=designation,
                joining_date=joined,
                salary=Decimal(salary),
                status=Staff.Status.ACTIVE if active else Staff.Status.INACTIVE,
                user=users.get(login),
                manager=users[manager].manager_profile,
                created_by_admin=users["alice_admin"].admin_profile,
            )
            employee, created = Staff.objects.get_or_create(email=email, defaults=data)
            if created:
                ok(f"Staff: {full_name}  ({designation})")
                continue
            # Fill in links missing from records seeded by older versions.
            updates = [
                field
                for field in ("user", "manager", "created_by_admin")
                if getattr(employee, f"{field}_id") is None and data[field]
            ]
            for field in updates:
                setattr(employee, field, data[field])
            if updates:
                employee.save(update_fields=updates)
            skip(f"Staff email {email}")

    def _seed_orders(self, products, admin, manager):
        from orders.models import Order, OrderItem

        self.heading("\n── orders.Order + OrderItem ────────────────")
        for index, (number, customer, product_index, quantity, status, ordered) in enumerate(ORDERS):
            creator = (
                {"created_by_manager": manager.manager_profile}
                if index < 3
                else {"created_by_admin": admin.admin_profile}
            )
            if Order.objects.filter(order_number=number).exists():
                Order.objects.filter(
                    order_number=number,
                    created_by_admin__isnull=True,
                    created_by_manager__isnull=True,
                ).update(**creator)
                skip(f"Order {number}")
                continue

            product = products[product_index]
            order = Order.objects.create(
                order_number=number,
                customer_name=customer,
                status=status,
                order_date=ordered,
                expected_delivery_date=(ordered + timedelta(days=7)).date(),
                **creator,
            )
            OrderItem.objects.create(
                order=order, product=product, quantity=quantity, unit_price=product.selling_price
            )
            order.recalculate_total()
            ok(
                f"Order {number}: {quantity} × {product.product_name} "
                f"({order.get_status_display()}, to {customer})"
            )

    def _seed_sales(self, products, admin):
        from sales.models import Sale, SaleItem

        self.heading("\n── sales.Sale + SaleItem ───────────────────")
        for number, sold_to, product_index, quantity, price, sold in SALES:
            if Sale.objects.filter(invoice_number=number).exists():
                Sale.objects.filter(
                    invoice_number=number, created_by_admin__isnull=True
                ).update(created_by_admin=admin.admin_profile)
                skip(f"Sale {number}")
                continue

            product = products[product_index]
            unit_price = Decimal(price)
            subtotal = quantity * unit_price
            # created_by_admin is also credited on the SALE stock movement.
            sale = Sale.objects.create(
                invoice_number=number,
                sold_to=sold_to,
                total_amount=subtotal,  # single line item
                sale_date=sold,
                created_by_admin=admin.admin_profile,
            )
            SaleItem.objects.create(  # save() deducts the stock
                sale=sale, product=product, quantity=quantity, unit_price=unit_price
            )
            ok(
                f"Sale {number}: {quantity} × {product.product_name} "
                f"@ {unit_price} = {subtotal}  (to {sold_to})"
            )

    def _seed_reports(self, admin, manager):
        from reports.models import SalesReport
        from sales.models import Sale, SaleItem

        self.heading("\n── reports.SalesReport ─────────────────────")
        records = [
            (admin, {"admin": admin.admin_profile}, date(2026, 7, 1), date(2026, 7, 31)),
            (manager, {"manager": manager.manager_profile}, date(2026, 7, 10), date(2026, 7, 20)),
        ]
        for user, generated_by, start, end in records:
            label = f"Sales report {start} – {end} by {user.username}"
            if SalesReport.objects.filter(start_date=start, end_date=end, **generated_by).exists():
                skip(label)
                continue

            sales = Sale.objects.filter(**day_range_filter("sale_date", start, end))
            revenue = sales.aggregate(revenue=Sum("total_amount"))["revenue"]
            items = SaleItem.objects.filter(sale__in=sales).aggregate(n=Sum("quantity"))["n"]
            SalesReport.objects.create(
                start_date=start,
                end_date=end,
                sales_count=sales.count(),
                items_sold=items or 0,
                total_revenue=revenue or Decimal("0"),
                **generated_by,
            )
            ok(label)

    def _seed_activity(self, users):
        from accounts.models import ActivityLog

        self.heading("\n── accounts.ActivityLog ────────────────────")
        if ActivityLog.objects.filter(user__in=users.values()).exists():
            skip("Activity log entries")
            return

        for username, action, target in ACTIVITY:
            user = users[username]
            ActivityLog.objects.create(
                user=user, role=user.role, action=action, target=target, ip_address="127.0.0.1"
            )
        ok(f"{len(ACTIVITY)} activity log entries")
