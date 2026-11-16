import { useEffect, useState } from "react";
import { useLoad } from "./api";
import { logout } from "./auth";
import { AlertsPage } from "./features/alerts/Alerts";
import { CaseDetail } from "./features/cases/CaseDetail";
import { CaseList } from "./features/cases/CaseList";
import { InstitutionList } from "./features/institutions/InstitutionList";
import { InstitutionProfile } from "./features/institutions/InstitutionProfile";
import { OverlapsPage } from "./features/overlaps/Overlaps";
import { ResolutionQueue } from "./features/institutions/ResolutionQueue";

type Me = { name: string; role: string };
const CAN_RESOLVE = ["officer", "bureau_head", "admin"];

function useHashRoute(): string {
  const [route, setRoute] = useState(window.location.hash.slice(1) || "/");
  useEffect(() => {
    const onChange = () => setRoute(window.location.hash.slice(1) || "/");
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}

// Feature screens live under src/features/<feature>/ and are routed here by URL hash.
export function App() {
  const route = useHashRoute();
  const { data: me } = useLoad<Me>("/me");
  const profileId = route.match(/^\/institutions\/([0-9a-f-]{36})$/)?.[1];
  const caseId = route.match(/^\/cases\/([0-9a-f-]{36})$/)?.[1];
  const caseList = route.match(/^\/cases(?:\?(.*))?$/);

  return (
    <>
      <header>
        <strong>SETHU</strong>
        <nav aria-label="Main">
          <a href="#/" aria-current={route === "/" || profileId ? "page" : undefined}>
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
          <a href="#/queue" aria-current={route === "/queue" ? "page" : undefined}>
            Unmatched names
          </a>
        </nav>
        <span>
          {me && `${me.name} (${me.role.replace("_", " ")})`}{" "}
          <button type="button" onClick={logout}>
            Sign out
          </button>
        </span>
      </header>
      <main>
        {caseId ? (
          <CaseDetail key={caseId} id={caseId} />
        ) : caseList ? (
          <CaseList key={route} initial={caseList[1] ?? ""} />
        ) : profileId ? (
          <InstitutionProfile id={profileId} />
        ) : route === "/alerts" ? (
          <AlertsPage />
        ) : route === "/overlaps" ? (
          <OverlapsPage canDetect={me?.role === "admin"} />
        ) : route === "/queue" ? (
          <ResolutionQueue canResolve={!!me && CAN_RESOLVE.includes(me.role)} />
        ) : (
          <InstitutionList />
        )}
      </main>
    </>
  );
}
