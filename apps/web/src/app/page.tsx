export default function Home() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-4 px-6 py-16">
      <h1 className="text-3xl font-semibold">APAAR-SDMV</h1>
      <p className="text-ink/80">
        Student Data Management &amp; Verification Platform — prototype
        foundation. The API is the source of truth; this console is built out in
        later phases.
      </p>
      <ul className="list-disc pl-5 text-sm">
        <li>API base path: `<code>/api/v1</code>` (health: `<code>GET /api/v1/health</code>`)</li>
        <li>All data is synthetic; all integrations are mock/sandbox.</li>
      </ul>
    </main>
  );
}
