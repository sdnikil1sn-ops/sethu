import { useEffect, useState } from "react";
import { useLoad } from "./api";
import { logout } from "./auth";
import { AlertsPage } from "./features/alerts/Alerts";
import { AuditLog } from "./features/audit/AuditLog";
import { CaseDetail } from "./features/cases/CaseDetail";
import { CaseList } from "./features/cases/CaseList";
import { Dashboard } from "./features/dashboard/Dashboard";
import { FindingsPage } from "./features/findings/Findings";
import { InstitutionList } from "./features/institutions/InstitutionList";
import { InstitutionProfile } from "./features/institutions/InstitutionProfile";
import { OverlapsPage } from "./features/overlaps/Overlaps";
import { ResolutionQueue } from "./features/institutions/ResolutionQueue";
import { ReportsPage } from "./features/reports/Reports";
import { SearchBox, SearchResults } from "./features/search/Search";

type Me = { name: string; role: string };
const CAN_RESOLVE = ["officer", "bureau_head", "admin"];
const CAN_AUDIT = ["auditor", "oversight", "admin"];
const CAN_DECIDE = ["bureau_head", "oversight"];

/** The route, and a count of hash changes. The case list rewrites its own address with replaceState
 * (no hashchange), so the stored route can be stale; `visit` changes whenever a link is followed. */
function useHashRoute(): { route: string; visit: number } {
  const [state, setState] = useState({ route: window.location.hash.slice(1) || "/", visit: 0 });
  useEffect(() => {
    const onChange = () => setState((s) => ({ route: window.location.hash.slice(1) || "/", visit: s.visit + 1 }));
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return state;
}

// Feature screens live under src/features/<feature>/ and are routed here by URL hash.
export function App() {
  const { route, visit } = useHashRoute();
  const { data: me } = useLoad<Me>("/me");
  const profileId = route.match(/^\/institutions\/([0-9a-f-]{36})$/)?.[1];
  const caseId = route.match(/^\/cases\/([0-9a-f-]{36})$/)?.[1];
  const caseList = route.match(/^\/cases(?:\?(.*))?$/);
  const searched = route.match(/^\/search\?(.*)$/) ? new URLSearchParams(route.split("?")[1]).get("q") ?? "" : null;

  return (
    <>
      <header>
        <strong>SETHU</strong>
        <nav aria-label="Main">
          <a href="#/" aria-current={route === "/" ? "page" : undefined}>
            Dashboard
          </a>
          <a href="#/institutions" aria-current={route === "/institutions" || profileId ? "page" : undefined}>
            Institutions
          </a>
          <a href="#/cases" aria-current={caseId || caseList ? "page" : undefined}>
            Cases
          </a>
          <a href="#/overlaps" aria-current={route === "/overlaps" ? "page" : undefined}>
            Overlaps
          </a>
          <a href="#/alerts" aria-current={route === "/alerts" ? "page" : undefined}>
            Alerts
          </a>
          <a href="#/findings" aria-current={route === "/findings" ? "page" : undefined}>
            Findings
          </a>
          <a href="#/queue" aria-current={route === "/queue" ? "page" : undefined}>
            Unmatched names
          </a>
          <a href="#/reports" aria-current={route === "/reports" ? "page" : undefined}>
            Reports
          </a>
          {me && CAN_AUDIT.includes(me.role) && (
            <a href="#/audit" aria-current={route === "/audit" ? "page" : undefined}>
              Audit log
            </a>
          )}
        </nav>
        <SearchBox key={searched ?? ""} initial={searched ?? ""} />
        <span>
          {me && `${me.name} (${me.role.replace("_", " ")})`}{" "}
          <button type="button" onClick={logout}>
            Sign out
          </button>
        </span>
      </header>
      <main>
        {searched !== null ? (
          <SearchResults key={searched} q={searched} />
        ) : caseId ? (
          <CaseDetail key={caseId} id={caseId} />
        ) : caseList ? (
          <CaseList key={visit} initial={caseList[1] ?? ""} />
        ) : profileId ? (
          <InstitutionProfile id={profileId} />
        ) : route === "/alerts" ? (
          <AlertsPage />
        ) : route === "/overlaps" ? (
          <OverlapsPage canDetect={me?.role === "admin"} />
        ) : route === "/queue" ? (
          <ResolutionQueue canResolve={!!me && CAN_RESOLVE.includes(me.role)} />
        ) : route === "/findings" ? (
          <FindingsPage canDecide={!!me && CAN_DECIDE.includes(me.role)} canDetect={me?.role === "admin"} />
        ) : route === "/reports" ? (
          <ReportsPage />
        ) : route === "/audit" ? (
          <AuditLog />
        ) : route === "/institutions" ? (
          <InstitutionList />
        ) : (
          <Dashboard />
        )}
      </main>
    </>
  );
}
