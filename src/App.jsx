
import { useEffect, useState } from "react";
import { ChevronRight, Search, Plus, Trash2 } from "lucide-react";
import Sidebar from "./Sidebar";

const inventoryItems = ["Drinking Water", "Food Packs", "First Aid Kits", "Medical Supplies"];
const inventoryWarehouses = ["WH-001", "WH-002", "WH-003", "WH-004", "WH-005"];
const requestShelters = [
  "Red Crecent Shelter",
  "Aman Shelter",
  "Al Awir Centre for Harboring",
  "Al Barsha Temporary Shelter",
];

const statusStyles = {
  "In Stock": "bg-green-50 text-green-600",
  "Low Stock": "bg-amber-50 text-amber-600",
  "Out Of Stock": "bg-red-50 text-red-600",
};

function StatCard({ title, value, color = "text-slate-900" }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-[17px] py-[16px] shadow-sm">
      <p className="mb-2 text-[11px] text-slate-500">
        {title}
      </p>

      <h2 className={`text-[24px] font-bold leading-7 ${color}`}>
        {value}
      </h2>
    </div>
  );
}

function InventoryPage({ authenticated, onRequestLogin }) {
  const [inventory, setInventory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [warehouseFilter, setWarehouseFilter] = useState("all");
  const [showAddForm, setShowAddForm] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [newItem, setNewItem] = useState({
    item_name: inventoryItems[0],
    quantity: "",
    warehouse_code: inventoryWarehouses[0],
  });

  useEffect(() => {
    let cancelled = false;

    async function loadInventory() {
      if (!authenticated) {
        setInventory([]);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError("");
      try {
        const response = await fetch("/warehouse", { credentials: "same-origin" });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Unable to load inventory.");
        if (!cancelled) setInventory(data);
      } catch (loadError) {
        if (!cancelled) setError(loadError.message || "Unable to connect to the inventory service.");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadInventory();
    return () => { cancelled = true; };
  }, [authenticated, refreshKey]);

  async function addStock(event) {
    event.preventDefault();
    setError("");
    try {
      const response = await fetch("/warehouse", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...newItem, quantity: Number(newItem.quantity) }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Unable to add stock.");
      setNewItem({
        item_name: inventoryItems[0],
        quantity: "",
        warehouse_code: inventoryWarehouses[0],
      });
      setShowAddForm(false);
      setRefreshKey((key) => key + 1);
    } catch (addError) {
      setError(addError.message || "Unable to add stock.");
    }
  }

  const filteredInventory = inventory.filter((product) => {
    const matchesSearch = product.item_name.toLowerCase().includes(search.toLowerCase());
    const matchesWarehouse = warehouseFilter === "all" || product.warehouse_code === warehouseFilter;
    return matchesSearch && matchesWarehouse;
  });
  const totalUnits = inventory.reduce((total, product) => total + product.quantity, 0);
  const lowStockCount = inventory.filter((product) => product.status === "Low Stock").length;
  const outOfStockCount = inventory.filter((product) => product.status === "Out Of Stock").length;

  return (
    <main className="min-h-[calc(100vh-78px)] bg-[#f7f9fc] px-[17px] py-[20px] text-[#101f3d] md:px-[30px]">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-[27px] font-bold tracking-tight">
            Inventory
          </h1>

          <p className="mt-1.5 text-[13px] text-[#7184a1]">
            Current stock across active warehouses.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowAddForm((visible) => !visible)}
          className="flex h-[39px] items-center gap-2 rounded-lg bg-[#2d5df1] px-[17px] text-[12px] font-semibold text-white shadow-md shadow-blue-200"
        >
          <Plus size={16} aria-hidden="true" />
          Add Stock
        </button>
      </div>

      <section className="mb-[18px] grid grid-cols-1 gap-[14px] md:grid-cols-3">
        <StatCard
          title="Total Units"
          value={totalUnits.toLocaleString()}
        />

        <StatCard
          title="Low Stock"
          value={lowStockCount}
          color="text-[#e87500]"
        />

        <StatCard
          title="Out Of Stock"
          value={outOfStockCount}
          color="text-[#eb3030]"
        />
      </section>

      {showAddForm && (
        <form onSubmit={addStock} className="mb-[18px] flex flex-wrap items-end gap-3 border-b border-[#dbe4f0] bg-white px-[18px] py-[16px]">
          <label className="flex min-w-[190px] flex-1 flex-col gap-1 text-[11px] font-semibold text-[#536989]">
            Item
            <select
              value={newItem.item_name}
              onChange={(event) => setNewItem({ ...newItem, item_name: event.target.value })}
              className="h-[36px] rounded-md border border-[#dbe4f0] bg-white px-2 text-[12px] text-[#101f3d]"
            >
              {inventoryItems.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
          <label className="flex w-[130px] flex-col gap-1 text-[11px] font-semibold text-[#536989]">
            Quantity
            <input
              type="number"
              min="0"
              required
              value={newItem.quantity}
              onChange={(event) => setNewItem({ ...newItem, quantity: event.target.value })}
              className="h-[36px] rounded-md border border-[#dbe4f0] px-2 text-[12px] text-[#101f3d]"
            />
          </label>
          <label className="flex min-w-[140px] flex-col gap-1 text-[11px] font-semibold text-[#536989]">
            Warehouse
            <select
              value={newItem.warehouse_code}
              onChange={(event) => setNewItem({ ...newItem, warehouse_code: event.target.value })}
              className="h-[36px] rounded-md border border-[#dbe4f0] bg-white px-2 text-[12px] text-[#101f3d]"
            >
              {inventoryWarehouses.map((warehouse) => <option key={warehouse}>{warehouse}</option>)}
            </select>
          </label>
          <button type="submit" className="h-[36px] rounded-md bg-[#2d5df1] px-4 text-[12px] font-semibold text-white">
            Save stock
          </button>
        </form>
      )}

      <section className="overflow-hidden rounded-xl border border-[#dbe4f0] bg-white shadow-sm">
        <div className="flex flex-wrap items-center gap-[10px] border-b border-slate-200 px-[18px] py-[14px]">
          <div className="flex h-[36px] w-full max-w-[340px] items-center gap-2 rounded-md border border-[#dbe4f0] px-3 text-[#8ca0bc]">
            <Search size={16} />

            <input
              type="text"
              placeholder="Search inventory..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              aria-label="Search inventory"
              className="w-full bg-transparent text-[12px] outline-none placeholder:text-[#9aaac0]"
            />
          </div>

          <select
            aria-label="Filter by warehouse"
            value={warehouseFilter}
            onChange={(event) => setWarehouseFilter(event.target.value)}
            className="h-[36px] rounded-md border border-[#dbe4f0] bg-white px-3 text-[11px] text-[#536989]"
          >
            <option value="all">All warehouses</option>
            {inventoryWarehouses.map((warehouse) => <option key={warehouse}>{warehouse}</option>)}
          </select>
        </div>

        {error && <p role="alert" className="border-b border-red-100 bg-red-50 px-[18px] py-3 text-[12px] text-red-700">{error}</p>}

        {!authenticated ? (
          <div className="px-5 py-12 text-center">
            <p className="text-[13px] text-[#536989]">Log in to view and manage inventory.</p>
            <button type="button" onClick={onRequestLogin} className="mt-3 text-[12px] font-semibold text-[#2d5df1]">Log in</button>
          </div>
        ) : isLoading ? (
          <p role="status" className="px-5 py-12 text-center text-[12px] text-[#7184a1]">Loading inventory...</p>
        ) : filteredInventory.length === 0 ? (
          <p className="px-5 py-12 text-center text-[12px] text-[#7184a1]">
            {inventory.length ? "No inventory matches your search." : "No inventory records yet."}
          </p>
        ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[750px] border-collapse text-left">
            <thead className="bg-[#f8fafc]">
              <tr className="border-b border-[#dbe4f0]">
                {[
                  "ITEM",
                  "WAREHOUSE",
                  "AVAILABLE QUANTITY",
                  "STATUS",
                ].map((heading) => (
                  <th
                    key={heading}
                    className="px-[14px] py-[13px] text-[10px] font-bold tracking-wide text-[#6a80a3]"
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {filteredInventory.map((product) => (
                <tr
                  key={product.warehouse_id}
                  className="h-[55px] border-b border-[#e9eef5] last:border-b-0"
                >
                  <td className="px-[14px] text-[11px] font-semibold">
                    {product.item_name}
                  </td>

                  <td className="px-[14px] font-mono text-[10px] text-[#465d80]">
                    {product.warehouse_code}
                  </td>

                  <td className="px-[14px] text-[11px]">
                    <span className="font-bold">
                      {product.quantity.toLocaleString()}
                    </span>
                    <span className="ml-1 text-[#607597]">
                      units
                    </span>
                  </td>

                  <td className="px-[14px]">
                    <span
                      className={`inline-flex rounded-full px-[9px] py-[5px] text-[10px] font-semibold ${
                        statusStyles[product.status]
                      }`}
                    >
                      {product.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        )}
      </section>
    </main>
  );
}


const urgencyStyles = {
  Critical: "bg-[#fff0f0] text-[#ef3030]",
  High: "bg-[#fff6ed] text-[#f06b13]",
  Moderate: "bg-[#fffaea] text-[#ca8b00]",
};

const requestStatusStyles = {
  pending: "bg-[#edf5ff] text-[#2863f5]",
  approved: "bg-[#fff9e9] text-[#d78a00]",
};

const requestStatuses = ["pending", "approved"];
const requestUrgencies = ["Critical", "High", "Moderate"];

function SupplyRequestsPage({ authenticated, onRequestLogin }) {
  const [requests, setRequests] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [search, setSearch] = useState("");
  const [urgencyFilter, setUrgencyFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showNewRequest, setShowNewRequest] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [newRequest, setNewRequest] = useState({
    shelter: "",
    item_name: "",
    quantity: "",
    urgency: "Moderate",
  });

  useEffect(() => {
    let cancelled = false;

    async function loadRequests() {
      if (!authenticated) {
        setRequests([]);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError("");
      try {
        const response = await fetch("/requests", { credentials: "same-origin" });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Unable to load requests.");
        if (!cancelled) setRequests(data);
      } catch (loadError) {
        if (!cancelled) setError(loadError.message || "Unable to connect to the requests service.");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadRequests();
    return () => { cancelled = true; };
  }, [authenticated, refreshKey]);

  async function createRequest(event) {
    event.preventDefault();
    setError("");
    try {
      const response = await fetch("/requests", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...newRequest, quantity: Number(newRequest.quantity) }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Unable to create request.");
      setNewRequest({ shelter: "", item_name: "", quantity: "", urgency: "Moderate" });
      setShowNewRequest(false);
      setRefreshKey((key) => key + 1);
    } catch (createError) {
      setError(createError.message || "Unable to create request.");
    }
  }

  async function updateRequestStatus(item, status) {
    setError("");
    setNotice("");
    try {
      const response = await fetch(`/requests/${item.request_id}`, {
        method: "PUT",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...item, status }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Unable to update request.");
      setRequests((current) => current.map((request) => (
        request.request_id === item.request_id
          ? { ...request, status: data.status, quantity: data.quantity }
          : request
      )));
      if (status === "approved") {
        if (data.fulfilled_quantity === 0) {
          setNotice("No matching inventory was available. The request remains pending.");
        } else if (data.status === "pending") {
          setNotice(`${data.fulfilled_quantity} supplied. ${data.quantity} remain pending.`);
        } else {
          setNotice(`${data.fulfilled_quantity} supplied. The request is fully approved.`);
        }
      }
    } catch (updateError) {
      setError(updateError.message || "Unable to update request.");
    }
  }

  async function deleteRequest(requestId) {
    if (!window.confirm("Delete this request?")) return;
    setError("");
    try {
      const response = await fetch(`/requests/${requestId}`, {
        method: "DELETE",
        credentials: "same-origin",
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Unable to delete request.");
      setRequests((current) => current.filter((request) => request.request_id !== requestId));
    } catch (deleteError) {
      setError(deleteError.message || "Unable to delete request.");
    }
  }

  const filteredRequests = requests.filter((request) => {
    const query = search.trim().toLowerCase();
    const matchesSearch = !query || [request.shelter, request.item_name, request.request_id]
      .some((value) => String(value ?? "").toLowerCase().includes(query));
    const matchesUrgency = urgencyFilter === "all" || request.urgency === urgencyFilter;
    const matchesStatus = statusFilter === "all" || request.status === statusFilter;
    return matchesSearch && matchesUrgency && matchesStatus;
  });

  return (
    <main className="min-h-[calc(100vh-78px)] bg-[#f7f9fc] px-[17px] py-[20px] text-[#101f3d] md:px-[30px]">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-[27px] font-bold tracking-tight">Supply Requests</h1>
          <p className="mt-1.5 text-[13px] text-[#7184a1]">Review and manage shelter supply needs.</p>
        </div>
        <button type="button" onClick={() => authenticated ? setShowNewRequest((visible) => !visible) : onRequestLogin()} className="flex h-[39px] items-center gap-2 rounded-lg bg-[#2d5df1] px-[17px] text-[12px] font-semibold text-white shadow-md shadow-blue-200">
          <Plus size={16} aria-hidden="true" />
          New Request
        </button>
      </div>

      {showNewRequest && (
        <form onSubmit={createRequest} className="mb-[18px] flex flex-wrap items-end gap-3 border-b border-[#dbe4f0] bg-white px-[18px] py-[16px]">
          <label className="flex min-w-[190px] flex-1 flex-col gap-1 text-[11px] font-semibold text-[#536989]">
            Shelter
            <select required value={newRequest.shelter} onChange={(event) => setNewRequest({ ...newRequest, shelter: event.target.value })} className="h-[36px] rounded-md border border-[#dbe4f0] bg-white px-2 text-[12px] text-[#101f3d]">
              <option value="" disabled>Select a shelter</option>
              {requestShelters.map((shelter) => <option key={shelter}>{shelter}</option>)}
            </select>
          </label>
          <label className="flex min-w-[180px] flex-1 flex-col gap-1 text-[11px] font-semibold text-[#536989]">
            Requested item
            <select required value={newRequest.item_name} onChange={(event) => setNewRequest({ ...newRequest, item_name: event.target.value })} className="h-[36px] rounded-md border border-[#dbe4f0] bg-white px-2 text-[12px] text-[#101f3d]">
              <option value="" disabled>Select an item</option>
              {inventoryItems.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
          <label className="flex w-[110px] flex-col gap-1 text-[11px] font-semibold text-[#536989]">
            Quantity
            <input type="number" min="1" required value={newRequest.quantity} onChange={(event) => setNewRequest({ ...newRequest, quantity: event.target.value })} className="h-[36px] rounded-md border border-[#dbe4f0] px-2 text-[12px] text-[#101f3d]" />
          </label>
          <label className="flex w-[130px] flex-col gap-1 text-[11px] font-semibold text-[#536989]">
            Urgency
            <select value={newRequest.urgency} onChange={(event) => setNewRequest({ ...newRequest, urgency: event.target.value })} className="h-[36px] rounded-md border border-[#dbe4f0] bg-white px-2 text-[12px] text-[#101f3d]">
              {requestUrgencies.map((urgency) => <option key={urgency}>{urgency}</option>)}
            </select>
          </label>
          <button type="submit" className="h-[36px] rounded-md bg-[#2d5df1] px-4 text-[12px] font-semibold text-white">Save request</button>
        </form>
      )}

      <section className="overflow-hidden rounded-xl border border-[#dbe4f0] bg-white shadow-sm">
        <div className="flex flex-wrap items-center gap-[10px] border-b border-[#dbe4f0] px-[18px] py-[15px]">
          <div className="flex h-[36px] w-full max-w-[340px] items-center gap-2 rounded-md border border-[#dbe4f0] px-3 text-[#8ca0bc]">
            <Search size={16} aria-hidden="true" />
            <input type="text" placeholder="Search requests..." value={search} onChange={(event) => setSearch(event.target.value)} aria-label="Search requests" className="w-full bg-transparent text-[12px] outline-none placeholder:text-[#9aaac0]" />
          </div>
          <select aria-label="Filter by urgency" value={urgencyFilter} onChange={(event) => setUrgencyFilter(event.target.value)} className="h-[36px] rounded-md border border-[#dbe4f0] bg-white px-3 text-[11px] text-[#536989]">
            <option value="all">All urgency</option>
            {requestUrgencies.map((urgency) => <option key={urgency}>{urgency}</option>)}
          </select>
          <select aria-label="Filter by status" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="h-[36px] rounded-md border border-[#dbe4f0] bg-white px-3 text-[11px] text-[#536989]">
            <option value="all">All statuses</option>
            {requestStatuses.map((status) => <option key={status} value={status}>{status[0].toUpperCase() + status.slice(1)}</option>)}
          </select>
        </div>

        {error && <p role="alert" className="border-b border-red-100 bg-red-50 px-[18px] py-3 text-[12px] text-red-700">{error}</p>}
        {notice && <p role="status" className="border-b border-green-100 bg-green-50 px-[18px] py-3 text-[12px] text-green-800">{notice}</p>}

        {!authenticated ? (
          <div className="px-5 py-12 text-center">
            <p className="text-[13px] text-[#536989]">Log in to view and manage requests.</p>
            <button type="button" onClick={onRequestLogin} className="mt-3 text-[12px] font-semibold text-[#2d5df1]">Log in</button>
          </div>
        ) : isLoading ? (
          <p role="status" className="px-5 py-12 text-center text-[12px] text-[#7184a1]">Loading requests...</p>
        ) : filteredRequests.length === 0 ? (
          <p className="px-5 py-12 text-center text-[12px] text-[#7184a1]">{requests.length ? "No requests match your filters." : "No requests yet."}</p>
        ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[1000px] border-collapse text-left">
            <thead className="bg-[#f8fafc]">
              <tr className="border-b border-[#dbe4f0]">
                {[
                  "REQUEST ID",
                  "SHELTER",
                  "REQUESTED ITEM",
                  "QUANTITY",
                  "URGENCY",
                  "STATUS",
                  "ACTIONS",
                ].map((heading) => (
                  <th key={heading} className="px-[14px] py-[13px] text-[10px] font-bold tracking-wide text-[#6a80a3]">
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredRequests.map((request) => (
                <tr key={request.request_id} className="h-[55px] border-b border-[#e9eef5] last:border-b-0">
                  <td className="px-[14px] font-mono text-[10px] font-semibold text-[#2d5df1]">REQ-{String(request.request_id).padStart(5, "0")}</td>
                  <td className="px-[14px] text-[11px] font-semibold text-[#111a2e]">{request.shelter || "Unspecified shelter"}</td>
                  <td className="px-[14px] text-[11px] text-[#536989]">{request.item_name}</td>
                  <td className="px-[14px] text-[11px] text-[#536989]">{request.quantity}</td>
                  <td className="px-[14px]">
                    <span className={`inline-flex rounded-full px-[9px] py-[5px] text-[10px] font-semibold ${urgencyStyles[request.urgency] || urgencyStyles.Moderate}`}>{request.urgency}</span>
                  </td>
                  <td className="px-[14px]">
                    <select aria-label={`Status for request ${request.request_id}`} value={request.status} disabled={request.status === "approved"} onChange={(event) => updateRequestStatus(request, event.target.value)} className={`rounded-full border-0 px-[9px] py-[5px] text-[10px] font-semibold disabled:cursor-not-allowed ${requestStatusStyles[request.status] || "bg-slate-100 text-slate-600"}`}>
                      {requestStatuses.map((status) => <option key={status} value={status}>{status[0].toUpperCase() + status.slice(1)}</option>)}
                    </select>
                  </td>
                  <td className="px-[14px] text-right">
                    <button type="button" onClick={() => deleteRequest(request.request_id)} title="Delete request" aria-label={`Delete request ${request.request_id}`} className="inline-flex h-8 w-8 items-center justify-center rounded-md text-[#7184a1] hover:bg-red-50 hover:text-red-600">
                      <Trash2 size={15} aria-hidden="true" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        )}
        {authenticated && !isLoading && (
        <div className="flex h-[52px] items-center border-t border-[#dbe4f0] px-[18px]">
          <p className="text-[10px] text-[#7184a1]">Showing {filteredRequests.length} of {requests.length} requests</p>
        </div>
        )}
      </section>
    </main>
  );
}

export default function App() {
  const [activePage, setActivePage] = useState("inventory");
  const [authenticated, setAuthenticated] = useState(false);
  const [checkingSession, setCheckingSession] = useState(true);
  const [showLogin, setShowLogin] = useState(false);
  const [loginName, setLoginName] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState("");

  useEffect(() => {
    fetch("/session", { credentials: "same-origin" })
      .then((response) => response.json())
      .then((data) => setAuthenticated(data.authenticated))
      .catch(() => setAuthenticated(false))
      .finally(() => setCheckingSession(false));
  }, []);

  function navigate(page) {
    setActivePage(page);
  }

  async function login(event) {
    event.preventDefault();
    setLoginError("");
    try {
      const response = await fetch("/login", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: loginName, password: loginPassword }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Unable to log in.");
      setAuthenticated(true);
      setShowLogin(false);
      setLoginPassword("");
    } catch (error) {
      setLoginError(error.message || "Unable to log in.");
    }
  }

  async function logout() {
    await fetch("/logout", { method: "POST", credentials: "same-origin" });
    setAuthenticated(false);
  }

  return (
    <div className="min-h-screen w-full bg-[#f7f9fc] text-[#111a2e]">
      <Sidebar
        activePage={activePage}
        onNavigate={navigate}
        mobileOpen={false}
        onClose={() => {}}
        authenticated={authenticated}
        onLogin={() => setShowLogin(true)}
        onLogout={logout}
      />

      <div className="min-h-screen min-w-0 md:ml-[239px]">
        <header className="flex h-[78px] items-center border-b border-[#dbe3ee] bg-white px-5 md:px-[30px]">
          <div className="truncate text-[12px] text-[#8196b5]">
            ReliefOps

            <ChevronRight
              size={13}
              className="mx-1 inline-block"
            />

            <span className="font-semibold capitalize text-[#344568]">
              {activePage}
            </span>
          </div>
        </header>

        {activePage === "inventory" && !checkingSession && (
          <InventoryPage authenticated={authenticated} onRequestLogin={() => setShowLogin(true)} />
        )}
        {(activePage === "requests" || activePage === "supply-requests") && !checkingSession && (
          <SupplyRequestsPage authenticated={authenticated} onRequestLogin={() => setShowLogin(true)} />
        )}

      </div>

      {showLogin && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-[#101827]/55 px-4" role="presentation">
          <form onSubmit={login} className="w-full max-w-[360px] rounded-lg border border-[#dbe4f0] bg-white p-6 shadow-xl" aria-labelledby="login-title">
            <h2 id="login-title" className="text-[18px] font-bold text-[#101f3d]">Log in</h2>
            <label className="mt-5 flex flex-col gap-1 text-[12px] font-semibold text-[#536989]">
              Name
              <input required autoComplete="username" value={loginName} onChange={(event) => setLoginName(event.target.value)} className="h-[38px] rounded-md border border-[#dbe4f0] px-3 text-[13px] text-[#101f3d]" />
            </label>
            <label className="mt-3 flex flex-col gap-1 text-[12px] font-semibold text-[#536989]">
              Password
              <input required type="password" autoComplete="current-password" value={loginPassword} onChange={(event) => setLoginPassword(event.target.value)} className="h-[38px] rounded-md border border-[#dbe4f0] px-3 text-[13px] text-[#101f3d]" />
            </label>
            {loginError && <p role="alert" className="mt-3 text-[12px] text-red-700">{loginError}</p>}
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" onClick={() => setShowLogin(false)} className="h-[36px] rounded-md px-3 text-[12px] text-[#536989]">Cancel</button>
              <button type="submit" className="h-[36px] rounded-md bg-[#2d5df1] px-4 text-[12px] font-semibold text-white">Log in</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
