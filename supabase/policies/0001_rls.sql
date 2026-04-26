alter table projects enable row level security;
alter table vendors enable row level security;
alter table evidences enable row level security;
alter table bank_transactions enable row level security;
alter table evidence_matches enable row level security;
alter table review_actions enable row level security;

-- MVP baseline policies.
-- Replace with project-membership policies once auth model is finalized.
create policy "service_role_all_projects" on projects
for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "service_role_all_vendors" on vendors
for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "service_role_all_evidences" on evidences
for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "service_role_all_bank_transactions" on bank_transactions
for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "service_role_all_evidence_matches" on evidence_matches
for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy "service_role_all_review_actions" on review_actions
for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
