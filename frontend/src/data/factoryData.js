export const inventory = [
  { item: 'Steel Sheets', quantity: 86, status: 'Available' },
  { item: 'M8 Bolts', quantity: 32, status: 'Low Stock' },
  { item: 'Paint Cans', quantity: 18, status: 'Available' },
];

export const orders = [
  { id: 'ORD-101', customer: 'Himalayan Traders', amount: 'Rs. 68,400', status: 'Pending' },
  { id: 'ORD-102', customer: 'Kathmandu Hardware', amount: 'Rs. 45,000', status: 'Processing' },
  { id: 'ORD-103', customer: 'Everest Supplies', amount: 'Rs. 13,600', status: 'Completed' },
];

export const employees = [
  { name: 'Sita Sharma', role: 'Staff', email: 'sita@factory.com' },
  { name: 'Ramesh Maharjan', role: 'Manager', email: 'ramesh@factory.com' },
  { name: 'Aarav Khadka', role: 'Admin', email: 'aarav@factory.com' },
];

export const menuByRole = {
  admin: ['Dashboard', 'Inventory', 'Orders', 'Sales', 'Reports', 'User Management'],
  manager: ['Dashboard', 'Inventory', 'Orders', 'Sales', 'Reports', 'Staff Records'],
  staff: ['Dashboard', 'My Profile', 'Inventory'],
};

export const roleNames = { admin: 'Admin', manager: 'Manager', staff: 'Staff' };
