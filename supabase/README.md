# Supabase Layout

- `migrations/`: schema and index migrations
- `policies/`: RLS and access policy SQL
- `seed/`: optional local/dev seed scripts

Apply in order:

1. `migrations/0001_init_schema.sql`
2. `policies/0001_rls.sql`
3. `seed/0001_seed.sql` (optional for local testing)
