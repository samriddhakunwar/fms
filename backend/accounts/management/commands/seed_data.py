"""
management/commands/seed_data.py
=================================
Populates the database with 5 realistic mock records for every model:

  • accounts.User          — 5 users (Admin, 2 × Inventory Manager, 2 × Employee)
  • inventory.Product      — 5 products (factory goods)
  • employees.Employee     — 5 employees (two linked to Employee logins)
  • salary.SalaryPayment   — 5 payments (one per employee)
  • orders.Order + Item    — 5 customer orders across the status range
  • sales.Sale + SaleItem  — 5 invoices with one line-item each

Usage:
    python manage.py seed_data

The command is idempotent: running it twice will not duplicate records —
it uses get_or_create / exists() guards on each unique field.
"""

from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ok(label: str) -> None:
    print(f"  ✅  {label}")


def skip(label: str) -> None:
    print(f"  ⏭   {label} (already exists)")


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Seed 5 mock records for every FMS model (accounts, inventory, employees, salary, sales)."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n🌱  Seeding FMS mock data …\n"))

        users     = self._seed_users()
        products  = self._seed_products()
        employees = self._seed_employees(users)
        self._seed_salary_payments(employees)
        self._seed_orders(products)
        self._seed_sales(products)

        self.stdout.write(self.style.SUCCESS("\n✔  Seeding complete.\n"))

    # ------------------------------------------------------------------
    # accounts.User
    # ------------------------------------------------------------------

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
                role=User.Role.INVENTORY_MANAGER,
                phone_number="01711-000002",
            ),
            dict(
                username="carol_inv",
                first_name="Carol",
                last_name="Akter",
                email="carol@fms.local",
                role=User.Role.INVENTORY_MANAGER,
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

        return users

    # ------------------------------------------------------------------
    # inventory.Product
    # ------------------------------------------------------------------

    def _seed_products(self):
        from inventory.models import Product

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
                quantity_in_stock=15,        # ← intentionally low to trigger ⚠ Low Stock
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
            product, created = Product.objects.get_or_create(sku=sku, defaults=data)
            if created:
                ok(f"Product: {product.product_name}  (SKU: {sku})")
            else:
                skip(f"Product SKU {sku}")
            products.append(product)

        return products

    # ------------------------------------------------------------------
    # employees.Employee
    # ------------------------------------------------------------------

    def _seed_employees(self, users):
        from employees.models import Employee

        self.stdout.write(self.style.HTTP_INFO("\n── employees.Employee ──────────────────────"))

        records = [
            dict(
                full_name="Md. Rafiqul Islam",
                email="rafiq@fms.local",
                phone="01811-100001",
                address="12, Mirpur Road, Dhaka",
                designation="Machine Operator",
                joining_date="2022-03-15",
                salary=Decimal("28000.00"),
                status=Employee.Status.ACTIVE,
            ),
            dict(
                full_name="Nasrin Khanam",
                email="nasrin@fms.local",
                phone="01811-100002",
                address="45, Gulshan Avenue, Dhaka",
                designation="Quality Inspector",
                joining_date="2021-07-01",
                salary=Decimal("32000.00"),
                status=Employee.Status.ACTIVE,
            ),
            dict(
                full_name="Karim Bepari",
                email="karim@fms.local",
                phone="01811-100003",
                address="7, BSCIC Industrial Area, Chittagong",
                designation="Warehouse Supervisor",
                joining_date="2020-01-10",
                salary=Decimal("38000.00"),
                status=Employee.Status.ACTIVE,
            ),
            dict(
                full_name="Ritu Rani Das",
                email="ritu@fms.local",
                phone="01811-100004",
                address="33, Tejgaon, Dhaka",
                designation="Production Technician",
                joining_date="2023-05-20",
                salary=Decimal("25000.00"),
                status=Employee.Status.ACTIVE,
            ),
            dict(
                full_name="Sohel Mahmud",
                email="sohel@fms.local",
                phone="01811-100005",
                address="22, Narayanganj Industrial Zone",
                designation="Maintenance Engineer",
                joining_date="2019-11-03",
                salary=Decimal("45000.00"),
                status=Employee.Status.INACTIVE,
            ),
        ]

        # The two STAFF logins get an HR record attached, so signing in as
        # dan_emp / eva_emp shows a real profile rather than the "ask an
        # administrator to link one" notice.
        by_username = {user.username: user for user in users}
        records[0]["user"] = by_username.get("dan_emp")
        records[1]["user"] = by_username.get("eva_emp")

        employees = []
        for data in records:
            email = data["email"]
            employee, created = Employee.objects.get_or_create(email=email, defaults=data)
            if not created and employee.user_id is None and data.get("user"):
                employee.user = data["user"]
                employee.save(update_fields=["user"])
            if created:
                ok(f"Employee: {employee.full_name}  ({employee.designation})")
            else:
                skip(f"Employee email {email}")
            employees.append(employee)

        return employees

    # ------------------------------------------------------------------
    # salary.SalaryPayment
    # ------------------------------------------------------------------

    def _seed_salary_payments(self, employees):
        from salary.models import SalaryPayment

        self.stdout.write(self.style.HTTP_INFO("\n── salary.SalaryPayment ────────────────────"))

        records = [
            dict(
                employee=employees[0],
                amount=Decimal("28000.00"),
                remarks="Regular July 2026 salary.",
            ),
            dict(
                employee=employees[1],
                amount=Decimal("32000.00"),
                remarks="Regular July 2026 salary.",
            ),
            dict(
                employee=employees[2],
                amount=Decimal("38000.00"),
                remarks="Regular July 2026 salary.",
            ),
            dict(
                employee=employees[3],
                amount=Decimal("26000.00"),    # 25 000 base + 1 000 attendance bonus
                remarks="July salary + BDT 1,000 attendance bonus.",
            ),
            dict(
                employee=employees[4],
                amount=Decimal("22500.00"),    # Pro-rated — inactive mid-month
                remarks="Final settlement — pro-rated for inactive status.",
            ),
        ]

        for data in records:
            # Uniqueness guard: skip if this exact payment was already seeded
            exists = SalaryPayment.objects.filter(**data).exists()

            if exists:
                skip(f"SalaryPayment for {data['employee'].full_name}")
            else:
                payment = SalaryPayment.objects.create(**data)
                ok(f"SalaryPayment: {payment.employee.full_name} — {payment.amount}")

    # ------------------------------------------------------------------
    # orders.Order + orders.OrderItem
    # ------------------------------------------------------------------

    def _seed_orders(self, products):
        """
        Customer orders. These deliberately do NOT move stock — an order is a
        commitment to supply, and the deduction happens when it is fulfilled
        and an invoice is raised (see orders.OrderViewSet.fulfil).
        """
        from orders.models import Order, OrderItem

        self.stdout.write(self.style.HTTP_INFO("\n── orders.Order + OrderItem ────────────────"))

        # Each tuple: (order_no, customer, product_index, qty, status, order_date)
        records = [
            ("ORD-2026-0001", "Shyam Pvt. Ltd.",               0, 20, Order.Status.PENDING,   timezone.datetime(2026, 8,  1,  9, 0, tzinfo=timezone.utc)),
            ("ORD-2026-0002", "Himalaya Trading Concern",      1, 12, Order.Status.CONFIRMED, timezone.datetime(2026, 8,  4, 11, 0, tzinfo=timezone.utc)),
            ("ORD-2026-0003", "Sita Hardware Suppliers",       2,  4, Order.Status.PENDING,   timezone.datetime(2026, 8,  9, 14, 0, tzinfo=timezone.utc)),
            ("ORD-2026-0004", "Gorkha Construction Pvt. Ltd.", 4, 60, Order.Status.CONFIRMED, timezone.datetime(2026, 8, 14, 10, 0, tzinfo=timezone.utc)),
            ("ORD-2026-0005", "Annapurna Steel Udhyog",        3, 10, Order.Status.CANCELLED, timezone.datetime(2026, 8, 20, 16, 0, tzinfo=timezone.utc)),
        ]

        for order_no, customer, prod_idx, qty, order_status, order_date in records:
            if Order.objects.filter(order_number=order_no).exists():
                skip(f"Order {order_no}")
                continue

            product = products[prod_idx]
            order = Order.objects.create(
                order_number=order_no,
                customer_name=customer,
                status=order_status,
                order_date=order_date,
                expected_delivery_date=(order_date + timezone.timedelta(days=7)).date(),
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

    # ------------------------------------------------------------------
    # sales.Sale + sales.SaleItem
    # ------------------------------------------------------------------

    def _seed_sales(self, products):
        from sales.models import Sale, SaleItem

        self.stdout.write(self.style.HTTP_INFO("\n── sales.Sale + SaleItem ───────────────────"))

        # Each tuple: (invoice_no, sold_to, product_index, qty, unit_price, sale_date)
        records = [
            ("INV-2026-0001", "Shyam Pvt. Ltd.",              0,  10, Decimal("1250.00"), timezone.datetime(2026, 7, 10, 9,  0, tzinfo=timezone.utc)),
            ("INV-2026-0002", "Himalaya Trading Concern",     1,   5, Decimal("875.50"),  timezone.datetime(2026, 7, 15, 11, 0, tzinfo=timezone.utc)),
            ("INV-2026-0003", "Sita Hardware Suppliers",      2,   3, Decimal("3400.00"), timezone.datetime(2026, 7, 20, 14, 0, tzinfo=timezone.utc)),
            ("INV-2026-0004", "Gorkha Construction Pvt. Ltd.", 4,  50, Decimal("540.00"),  timezone.datetime(2026, 7, 25, 10, 0, tzinfo=timezone.utc)),
            ("INV-2026-0005", "Annapurna Steel Udhyog",       0,   8, Decimal("1300.00"), timezone.datetime(2026, 7, 30, 16, 0, tzinfo=timezone.utc)),
        ]

        for inv_no, sold_to, prod_idx, qty, unit_price, sale_date in records:
            if Sale.objects.filter(invoice_number=inv_no).exists():
                skip(f"Sale {inv_no}")
                continue

            product = products[prod_idx]

            # Create the Sale header first (total_amount starts at 0; app code
            # should update it — here we set it to the single-item subtotal)
            subtotal = qty * unit_price
            sale = Sale.objects.create(
                invoice_number=inv_no,
                sold_to=sold_to,
                total_amount=subtotal,   # Single line item; equals the subtotal
                sale_date=sale_date,
            )

            # Create the line item — SaleItem.save() will:
            #   1. Check stock availability
            #   2. Compute subtotal (quantity × unit_price)
            #   3. Deduct quantity from product.quantity_in_stock
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
