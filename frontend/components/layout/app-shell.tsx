"use client";

import type { ReactNode } from "react";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { navigation, studentNavigation } from "@/components/navigation/navigation-data";
import { NavIcon } from "@/components/navigation/nav-icon";
import { ApiConnectionIndicator } from "@/components/shared/api-connection-indicator";
import { ApiHealthProvider, useApiHealth } from "@/hooks/use-api-health";
import { LearnerSelectionProvider } from "@/hooks/use-learner-selection";

function Mark() {
  return <span className="brand-mark" aria-hidden="true"><span/><span/><span/><span/></span>;
}

function Sidebar({ collapsed, onToggle, onNavigate }: { collapsed: boolean; onToggle: () => void; onNavigate?: () => void }) {
  const pathname = usePathname();
  const inStudentStudio = pathname.startsWith("/studio");
  const workspaceNavigation = inStudentStudio ? studentNavigation : navigation;
  const connection = useApiHealth();
  const contextLabel = inStudentStudio ? "Student activity · local demo" : connection.state === "mock" ? "Synthetic demonstration" : connection.state === "connected" ? "Backend API workspace" : "API workspace";
  const modeLabel = connection.state === "mock" ? "Mock mode" : connection.state === "connected" ? "API connected" : connection.state === "connecting" ? "Connecting" : "API unavailable";
  return (
    <aside className={`sidebar ${collapsed ? "sidebar--collapsed" : ""}`} aria-label="Main navigation">
      <div className="sidebar-brand">
        <Link href={inStudentStudio ? "/studio" : "/"} className="brand-link" aria-label={inStudentStudio ? "Student Learning Studio home" : "MCP-RI research overview"} onClick={onNavigate}>
          <Mark />
          {!collapsed && <span className="brand-copy"><strong>MCP-RI</strong><small>Learning intelligence</small></span>}
        </Link>
        <button className="icon-button sidebar-toggle" onClick={onToggle} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} title={collapsed ? "Expand sidebar" : "Collapse sidebar"}>
          <svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="m14 5-7 7 7 7"/></svg>
        </button>
      </div>
      <div className="sidebar-context">
        {!collapsed ? <><span className="context-dot"/><span>{contextLabel}</span></> : <span className="context-dot" title={contextLabel}/> }
      </div>
      <nav id="primary-navigation" className="nav-groups">
        {workspaceNavigation.map((group) => <div className="nav-group" key={group.label}>
          {!collapsed && <p className="nav-group-title">{group.label}</p>}
          <ul>{group.items.map((item) => {
            const inExploreFlow = item.href === "/studio/explore" && /^\/studio\/(subjects|topics|lessons|practice)(\/|$)/.test(pathname);
            const active = item.href === "/" || item.href === "/studio" ? pathname === item.href : pathname === item.href || pathname.startsWith(`${item.href}/`) || inExploreFlow;
            return <li key={item.href}><Link href={item.href} onClick={onNavigate} className={`nav-link ${active ? "nav-link--active" : ""}`} aria-current={active ? "page" : undefined} title={collapsed ? item.label : undefined}>
              <NavIcon name={item.icon}/><span className="nav-link-label">{item.label}</span>{active && <span className="nav-active-mark"/>}
            </Link></li>;
          })}</ul>
        </div>)}
      </nav>
      <Link className="nav-link workspace-switch" href={inStudentStudio ? "/" : "/studio"} onClick={onNavigate} title={collapsed ? "Switch workspace" : undefined}>
        <NavIcon name={inStudentStudio ? "research" : "book"}/><span className="nav-link-label">{inStudentStudio ? "Research workspace" : "Student learning studio"}</span><span className="nav-active-mark"/>
      </Link>
      {!collapsed && <div className="sidebar-footnote"><div className="footnote-mark"><span>i</span></div><div><strong>{inStudentStudio ? "Local demo profile" : "Research prototype"}</strong><p>{inStudentStudio ? "Activity is saved locally and kept separate from EdNet." : "Estimates are provisional. Activities may be unavailable."}</p></div></div>}
      <div className="sidebar-bottom"><span className="avatar avatar--small">{inStudentStudio ? "LD" : "MR"}</span>{!collapsed && <span><strong>{inStudentStudio ? "Local demo profile" : "Research workspace"}</strong><small>{inStudentStudio ? "Not an authenticated account" : modeLabel}</small></span>}</div>
    </aside>
  );
}

function AppShellLayout({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();
  const inStudentStudio = pathname.startsWith("/studio");
  const workspaceNavigation = inStudentStudio ? studentNavigation : navigation;
  const allItems = workspaceNavigation.flatMap((group) => group.items);
  const current = allItems.find((item) => item.href === pathname || (item.href !== "/" && pathname.startsWith(`${item.href}/`))) ?? allItems[0];
  const dynamicTitle = inStudentStudio
    ? pathname.includes("/practice/") ? "Practice" : pathname.includes("/lessons/") ? "Lesson" : pathname.includes("/topics/") ? "Topic" : pathname.includes("/subjects/") ? "Subject" : null
    : null;
  const title = dynamicTitle ?? current.label;
  const parent = inStudentStudio ? "Student learning studio" : navigation.find((group) => group.items.includes(current))?.label;

  useEffect(() => {
    if (!mobileOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setMobileOpen(false);
      document.querySelector<HTMLButtonElement>(".mobile-menu-button")?.focus();
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [mobileOpen]);

  return <div className="app-frame">
    <a className="skip-link" href="#main-content">Skip to content</a>
    {mobileOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)}/>}
    <div className={`sidebar-wrap ${mobileOpen ? "sidebar-wrap--open" : ""}`}><Sidebar collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} onNavigate={() => setMobileOpen(false)}/></div>
    <div className="app-main">
      <header className="topbar">
        <div className="topbar-left">
          <button className="icon-button mobile-menu-button" aria-label={mobileOpen ? "Close navigation" : "Open navigation"} aria-controls="primary-navigation" aria-expanded={mobileOpen} onClick={() => setMobileOpen((open) => !open)}><span className="menu-glyph"><i/><i/><i/></span></button>
          <div className="page-heading"><div className="breadcrumbs"><span>{parent}</span><span className="crumb-separator">/</span><span>{title}</span></div><h1>{title}</h1></div>
        </div>
        <div className="topbar-right"><ApiConnectionIndicator/><div className="profile-button" title={inStudentStudio ? "Local demo profile" : "Research workspace"}><span className="avatar">{inStudentStudio ? "LD" : "MR"}</span><span className="profile-label">{inStudentStudio ? "Local demo profile" : "Research workspace"}</span><span className="chevron" aria-hidden="true">⌄</span></div></div>
      </header>
      <main id="main-content" className="main-content" tabIndex={-1}>{children}</main>
      <footer className="app-footer"><span>MCP-RI <span className="footer-divider">·</span> {inStudentStudio ? "Student Learning Studio" : "Research interface prototype"}</span><span>{inStudentStudio ? "Curated lessons · locally saved activity" : "Evidence first. Interpretations remain provisional."}</span></footer>
    </div>
  </div>;
}

export function AppShell({ children }: { children: ReactNode }) {
  return <ApiHealthProvider><LearnerSelectionProvider><Suspense fallback={<div className="app-frame"><main id="main-content" className="main-content">{children}</main></div>}><AppShellLayout>{children}</AppShellLayout></Suspense></LearnerSelectionProvider></ApiHealthProvider>;
}
