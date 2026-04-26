insert into projects (name, code, start_date, end_date, manager_name, status)
values
  ('Sample Construction A', 'PRJ-001', '2026-01-01', '2026-12-31', 'Kim PM', 'ongoing')
on conflict (code) do nothing;

insert into vendors (name, alias, business_number)
values
  ('ABC STEEL', 'ABC', '123-45-67890'),
  ('HAN RIVER ELECTRIC', 'HRE', '223-55-77880')
on conflict do nothing;
