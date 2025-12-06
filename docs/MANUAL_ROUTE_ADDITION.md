# Project Management UI - Manual Route Addition

## Add this route to App.tsx

Insert the following route **before** the catch-all route (line 130):

```typescript
<Route path="/projects" element={
  <ProtectedRoute>
    <Layout><ProjectsPage /></Layout>
  </ProtectedRoute>
} />
```

### Full Routes Section (lines 75-135)

```typescript
function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/" element={
        <ProtectedRoute>
          <Layout><DashboardPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/events" element={
        <ProtectedRoute>
          <Layout><EventsPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/traces" element={
        <ProtectedRoute>
          <Layout><TracesPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/traces/:traceId" element={
        <ProtectedRoute>
          <Layout><TraceView /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/alerts" element={
        <ProtectedRoute>
          <Layout><AlertsPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/prompts" element={
        <ProtectedRoute>
          <Layout><PromptsPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/prompts/:promptName" element={
        <ProtectedRoute>
          <Layout><PromptDetailPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/settings" element={
        <ProtectedRoute>
          <Layout><SettingsPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/billing" element={
        <ProtectedRoute>
          <Layout><BillingPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/usage" element={
        <ProtectedRoute>
          <Layout><UsagePage /></Layout>
        </ProtectedRoute>
      } />
      {/* ADD THIS ROUTE */}
      <Route path="/projects" element={
        <ProtectedRoute>
          <Layout><ProjectsPage /></Layout>
        </ProtectedRoute>
      } />
      {/* END OF NEW ROUTE */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
```

## Status

✅ ProjectsPage.tsx created
✅ Import added to App.tsx
✅ Navigation link added
⏭️ Route needs to be added manually (see above)

The route addition is straightforward - just copy the route block above and paste it before the catch-all route in App.tsx.
