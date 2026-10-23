// SPDX-License-Identifier: Apache-2.0
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthProvider";
import { Layout, RequireAuth } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { ReferencePage } from "./pages/ReferencePage";
import { AddressesPage } from "./features/ipaddresses/AddressesPage";
import { PrefixDetailPage } from "./features/prefixes/PrefixDetailPage";
import { PrefixesPage } from "./features/prefixes/PrefixesPage";
import { SearchPage } from "./features/search/SearchPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<RequireAuth />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/prefixes" replace />} />
              <Route path="/prefixes" element={<PrefixesPage />} />
              <Route path="/prefixes/:id" element={<PrefixDetailPage />} />
              <Route path="/ip-addresses" element={<AddressesPage />} />
              <Route
                path="/vrfs"
                element={
                  <ReferencePage
                    config={{
                      endpoint: "vrfs",
                      title: "VRFs",
                      extraField: { field: "rd", label: "Route Distinguisher", type: "text" },
                    }}
                  />
                }
              />
              <Route
                path="/vlans"
                element={
                  <ReferencePage
                    config={{
                      endpoint: "vlans",
                      title: "VLANs",
                      extraField: { field: "vid", label: "VID", type: "number" },
                    }}
                  />
                }
              />
              <Route path="/search" element={<SearchPage />} />
              <Route
                path="/organizations"
                element={<ReferencePage config={{ endpoint: "organizations", title: "Organizations" }} />}
              />
              <Route
                path="/tenants"
                element={
                  <ReferencePage
                    config={{
                      endpoint: "tenants",
                      title: "Tenants",
                      foreignKey: { field: "organization", label: "Organization", optionsEndpoint: "organizations" },
                    }}
                  />
                }
              />
              <Route
                path="/regions"
                element={<ReferencePage config={{ endpoint: "regions", title: "Regions" }} />}
              />
              <Route
                path="/sites"
                element={
                  <ReferencePage
                    config={{
                      endpoint: "sites",
                      title: "Sites",
                      foreignKey: { field: "region", label: "Region", optionsEndpoint: "regions" },
                    }}
                  />
                }
              />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
