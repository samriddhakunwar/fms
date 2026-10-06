from datetime import date
from decimal import Decimal
from typing import Any

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from fms.dates import day_range_filter


# Helpers
def ok(label: str) -> None:
    print(f"  ✅  {label}")


def skip(label: str) -> None:
    print(f"  ⏭   {label} (already exists)")


# Command
class Command(BaseCommand):
    help = (
        "Seed mock records for every FMS model (accounts, inventory, employees, "
        "orders, sales, reports, activity log)."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n🌱  Seeding FMS mock data …\n"))

        users     = self._seed_users()
        by_username = {user.username: user for user in users}
        admin     = by_username["alice_admin"]
        manager   = by_username["bob_inv"]
        products  = self._seed_products(admin)
        self._seed_staff(users)
        self._seed_orders(products, admin, manager)
        self._seed_sales(products, admin)
        self._seed_reports(admin, manager)
        self._seed_activity(by_username)

        self.stdout.write(self.style.SUCCESS("\n✔  Seeding complete.\n"))

    # accounts.User
    def _seed_users(self):
        from accounts.models import User

        self.stdout.write(self.style.HTTP_INFO("── accounts.User ──────────────────────────"))

        records = [
            dict(
                username="alice_admin",
                first_name="Alice",
                last_name="Rahman",
                email="alice@fms.local",
                role=User.Role.ADMIN,
                phone_number="01711-000001",
                is_staff=True,
            ),
            dict(
                username="bob_inv",
                first_name="Bob",
                last_name="Hossain",
                email="bob@fms.local",
                role=User.Role.MANAGER,
                phone_number="01711-000002",
            ),
            dict(
                username="carol_inv",
                first_name="Carol",
                last_name="Akter",
                email="carol@fms.local",
                role=User.Role.MANAGER,
                phone_number="01711-000003",
            ),
            dict(
                username="dan_emp",
                first_name="Dan",
                last_name="Miah",
                email="dan@fms.local",
                role=User.Role.STAFF,
                phone_number="01711-000004",
            ),
            dict(
                username="eva_emp",
                first_name="Eva",
                last_name="Begum",
                email="eva@fms.local",
                role=User.Role.STAFF,
                phone_number="01711-000005",
            ),
        ]

        users = []
        for data in records:
            username = data.pop("username")
            if User.objects.filter(username=username).exists():
                skip(f"User: {username}")
                users.append(User.objects.get(username=username))
            else:
                user = User.objects.create(
                    username=username,
                    password=make_password("FMS@1234"),   # same password for all seed users
                    **data,
                )
                ok(f"User: {username}  ({user.get_role_display()})")
                users.append(user)

        # Managers were created by the seeded Admin.
        from accounts.models import ManagerProfile

        admin_profile = users[0].admin_profile
        ManagerProfile.objects.filter(
            user__in=users, created_by_admin__isnull=True
        ).update(created_by_admin=admin_profile)

        return users

    # inventory.Product
    def _seed_products(self, admin):
        from inventory.models import Product, StockMovement

        self.stdout.write(self.style.HTTP_INFO("\n── inventory.Product ───────────────────────"))

        records = [
            dict(
                sku="PRD-001",
                product_name="Industrial Bolt Set (M12)",
                description="High-tensile steel bolts used in heavy machinery assemblies.",
                selling_price=Decimal("1250.00"),
                quantity_in_stock=500,
                minimum_stock_level=50,
            ),
            dict(
                sku="PRD-002",
                product_name="Bearing Unit 6205",
                description="Deep-groove ball bearing for conveyor belt rollers.",
                selling_price=Decimal("875.50"),
                quantity_in_stock=200,
                minimum_stock_level=30,
            ),
            dict(
                sku="PRD-003",
                product_name="Hydraulic Seal Kit",
                description="Replacement seal kit for hydraulic press cylinders.",
                selling_price=Decimal("3400.00"),
                quantity_in_stock=80,
                minimum_stock_level=10,
            ),
            dict(
                sku="PRD-004",
                product_name="Safety Gloves (Leather)",
                description="Heat-resistant leather gloves for welding and cutting tasks.",
                selling_price=Decimal("320.00"),
                quantity_in_stock=15,
                minimum_stock_level=20,
            ),
            dict(
                sku="PRD-005",
                product_name="Welding Electrode E6013",
                description="General-purpose mild-steel welding electrode, 3.2 mm diameter.",
                selling_price=Decimal("540.00"),
                quantity_in_stock=1000,
                minimum_stock_level=100,
            ),
        ]

        products = []
        for data in records:
            sku = data["sku"]
            product, created = Product.objects.get_or_create(
                sku=sku, defaults={**data, "created_by_admin": admin.admin_profile}
            )
            if created:
                StockMovement.record(
                    product,
                    product.quantity_in_stock,
                    StockMovement.MovementType.STOCK_IN,
                    admin,
                    "Opening stock",
                )
                ok(f"Product: {product.product_name}  (SKU: {sku})")
            else:
                if product.created_by_admin_id is None and product.created_by_manager_id is None:
                    product.created_by_admin = admin.admin_profile
                    product.save(update_fields=["created_by_admin"])
                skip(f"Product SKU {sku}")
            products.append(product)

        return products

    # employees.Staff
    def _seed_staff(self, users):
        from employees.models import Staff

        self.stdout.write(self.style.HTTP_INFO("\n── employees.Staff ─────────────────────────"))

        records: list[dict[str, Any]] = [
            dict(
                full_name="Md. Rafiqul Islam",
                email="rafiq@fms.local",
                phone="01811-100001",
                address="12, Mirpur Road, Dhaka",
                designation="Machine Operator",
                joining_date="2022-03-15",
                salary=Decimal("28000.00"),
                status=Staff.Status.ACTIVE,
            ),
            dict(
                full_name="Nasrin Khanam",
                email="nasrin@fms.local",
                phone="01811-100002",
                address="45, Gulshan Avenue, Dhaka",
                designation="Quality Inspector",
                joining_date="2021-07-01",
                salary=Decimal("32000.00"),
                status=Staff.Status.ACTIVE,
            ),
            dict(
                full_name="Karim Bepari",
                email="karim@fms.local",
                phone="01811-100003",
                address="7, BSCIC Industrial Area, Chittagong",
                designation="Warehouse Supervisor",
                joining_date="2020-01-10",
                salary=Decimal("38000.00"),
                status=Staff.Status.ACTIVE,
            ),
            dict(
                full_name="Ritu Rani Das",
                email="ritu@fms.local",
                phone="01811-100004",
                address="33, Tejgaon, Dhaka",
                designation="Production Technician",
                joining_date="2023-05-20",
                salary=Decimal("25000.00"),
                status=Staff.Status.ACTIVE,
            ),
            dict(
                full_name="Sohel Mahmud",
                email="sohel@fms.local",
                phone="01811-100005",
                address="22, Narayanganj Industrial Zone",
                designation="Maintenance Engineer",
                joining_date="2019-11-03",
                salary=Decimal("45000.00"),
                status=Staff.Status.INACTIVE,
            ),
        ]

        by_username = {user.username: user for user in users}
        records[0]["user"] = by_username.get("dan_emp")
        records[1]["user"] = by_username.get("eva_emp")

        # Bob manages the first three, Carol the last two; all added by Alice.
        bob = by_username["bob_inv"].manager_profile
        carol = by_username["carol_inv"].manager_profile
        for index, data in enumerate(records):
            data["manager"] = bob if index < 3 else carol
            data["created_by_admin"] = by_username["alice_admin"].admin_profile

        employees = []
        for data in records:
            email = data["email"]
            employee, created = Staff.objects.get_or_create(email=email, defaults=data)
            if not created:
                updates = [
                    field
                    for field in ("user", "manager", "created_by_admin")
                    if getattr(employee, f"{field}_id") is None and data.get(field)
                ]
                for field in updates:
                    setattr(employee, field, data[field])
                if updates:
                    employee.save(update_fields=updates)
            if created:
                ok(f"Staff: {employee.full_name}  ({employee.designation})")
            else:
                skip(f"Staff email {email}")
            employees.append(employee)

        return employees

    # orders.Order + orders.OrderItem
    def _seed_orders(self, products, admin, manager):
        from orders.models import Order, OrderItem

        self.stdout.write(self.style.HTTP_INFO("\n── orders.Order + OrderItem ────────────────"))

        records = [
            ("ORD-2026-0001", "Shyam Pvt. Ltd.",               0, 20, Order.Status.PENDING,   timezone.datetime(2026, 8,  1,  9, 0, tzinfo=timezone.utc)),
            ("ORD-2026-0002", "Himalaya Trading Concern",      1, 12, Order.Status.CONFIRMED, timezone.datetime(2026, 8,  4, 11, 0, tzinfo=timezone.utc)),
            ("ORD-2026-0003", "Sita Hardware Suppliers",       2,  4, Order.Status.PENDING,   timezone.datetime(2026, 8,  9, 14, 0, tzinfo=timezone.utc)),
            ("ORD-2026-0004", "Gorkha Construction Pvt. Ltd.", 4, 60, Order.Status.CONFIRMED, timezone.datetime(2026, 8, 14, 10, 0, tzinfo=timezone.utc)),
            ("ORD-2026-0005", "Annapurna Steel Udhyog",        3, 10, Order.Status.CANCELLED, timezone.datetime(2026, 8, 20, 16, 0, tzinfo=timezone.utc)),
        ]

        # Bob (Manager) took the first three orders, Alice (Admin) the rest.
        for index, (order_no, customer, prod_idx, qty, order_status, order_date) in enumerate(records):
            creator = (
                {"created_by_manager": manager.manager_profile}
                if index < 3
                else {"created_by_admin": admin.admin_profile}
            )
            if Order.objects.filter(order_number=order_no).exists():
                Order.objects.filter(
                    order_number=order_no,
                    created_by_admin__isnull=True,
                    created_by_manager__isnull=True,
                ).update(**creator)
                skip(f"Order {order_no}")
                continue

            product = products[prod_idx]
            order = Order.objects.create(
                order_number=order_no,
                customer_name=customer,
                status=order_status,
                order_date=order_date,
                expected_delivery_date=(order_date + timezone.timedelta(days=7)).date(),
                **creator,
            )
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                unit_price=product.selling_price,
            )
            order.recalculate_total()

            ok(
                f"Order {order_no}: {qty} × {product.product_name} "
                f"({order.get_status_display()}, to {customer})"
            )

    # sales.Sale + sales.SaleItem
    def _seed_sales(self, products, admin):
        from sales.models import Sale, SaleItem

        self.stdout.write(self.style.HTTP_INFO("\n── sales.Sale + SaleItem ───────────────────"))

        records = [
            ("INV-2026-0001", "Shyam Pvt. Ltd.",              0,  10, Decimal("1250.00"), timezone.datetime(2026, 7, 10, 9,  0, tzinfo=timezone.utc)),
            ("INV-2026-0002", "Himalaya Trading Concern",     1,   5, Decimal("875.50"),  timezone.datetime(2026, 7, 15, 11, 0, tzinfo=timezone.utc)),
            ("INV-2026-0003", "Sita Hardware Suppliers",      2,   3, Decimal("3400.00"), timezone.datetime(2026, 7, 20, 14, 0, tzinfo=timezone.utc)),
            ("INV-2026-0004", "Gorkha Construction Pvt. Ltd.", 4,  50, Decimal("540.00"),  timezone.datetime(2026, 7, 25, 10, 0, tzinfo=timezone.utc)),
            ("INV-2026-0005", "Annapurna Steel Udhyog",       0,   8, Decimal("1300.00"), timezone.datetime(2026, 7, 30, 16, 0, tzinfo=timezone.utc)),
        ]

        for inv_no, sold_to, prod_idx, qty, unit_price, sale_date in records:
            if Sale.objects.filter(invoice_number=inv_no).exists():
                Sale.objects.filter(
                    invoice_number=inv_no, created_by_admin__isnull=True
                ).update(created_by_admin=admin.admin_profile)
                skip(f"Sale {inv_no}")
                continue

            product = products[prod_idx]

            subtotal = qty * unit_price
            sale = Sale.objects.create(
                invoice_number=inv_no,
                sold_to=sold_to,
                total_amount=subtotal,   # Single line item; equals the subtotal
                sale_date=sale_date,
                created_by_admin=admin.admin_profile,  # Also credited on the SALE stock movement
            )

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=qty,
                unit_price=unit_price,
                subtotal=subtotal,       # Provide explicitly; save() overwrites it anyway
            )

            ok(
                f"Sale {inv_no}: {qty} × {product.product_name} "
                f"@ {unit_price} = {subtotal}  (to {sold_to})"
            )

    # reports.SalesReport
    def _seed_reports(self, admin, manager):
        from reports.models import SalesReport
        from sales.models import Sale, SaleItem

        self.stdout.write(self.style.HTTP_INFO("\n── reports.SalesReport ─────────────────────"))

        records = [
            (admin, {"admin": admin.admin_profile}, date(2026, 7, 1), date(2026, 7, 31)),
            (manager, {"manager": manager.manager_profile}, date(2026, 7, 10), date(2026, 7, 20)),
        ]
        for user, generated_by, start, end in records:
            if SalesReport.objects.filter(start_date=start, end_date=end, **generated_by).exists():
                skip(f"Sales report {start} – {end} by {user.username}")
                continue

            window = day_range_filter("sale_date", start, end)
            sales = Sale.objects.filter(**window)
            totals = sales.aggregate(revenue=Sum("total_amount"))
            items = SaleItem.objects.filter(sale__in=sales).aggregate(n=Sum("quantity"))
            SalesReport.objects.create(
                start_date=start,
                end_date=end,
                sales_count=sales.count(),
                items_sold=items["n"] or 0,
                total_revenue=totals["revenue"] or Decimal("0"),
                **generated_by,
            )
            ok(f"Sales report {start} – {end} by {user.username}")

    # accounts.ActivityLog
    def _seed_activity(self, by_username):
        from accounts.models import ActivityLog

        self.stdout.write(self.style.HTTP_INFO("\n── accounts.ActivityLog ────────────────────"))

        if ActivityLog.objects.filter(user__in=by_username.values()).exists():
            skip("Activity log entries")
            return

        Action = ActivityLog.Action
        entries = [
            ("alice_admin", Action.LOGIN, ""),
            ("bob_inv", Action.LOGIN, ""),
            ("bob_inv", Action.VIEW, "staff"),
            ("bob_inv", Action.VIEW, "sale"),
            ("dan_emp", Action.LOGIN_FAILED, ""),
            ("dan_emp", Action.LOGIN, ""),
            ("dan_emp", Action.VIEW, "product"),
            ("dan_emp", Action.VIEW, "staff"),
            ("dan_emp", Action.LOGOUT, ""),
            ("bob_inv", Action.LOGOUT, ""),
        ]
        for username, action, target in entries:
            user = by_username[username]
            ActivityLog.objects.create(
                user=user, role=user.role, action=action, target=target, ip_address="127.0.0.1"
            )
        ok(f"{len(entries)} activity log entries")
