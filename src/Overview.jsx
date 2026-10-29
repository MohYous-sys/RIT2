
import { useEffect, useState } from "react";
import {
  FileText,
  Package,
  AlertTriangle,
  Users,
  ChevronRight,
  X,
} from "lucide-react";

const statDefinitions = [
  {
    label: "Open Requests",
    icon: FileText,
    iconColor: "text-blue-600",
    iconBackground: "bg-blue-50",
  },
  {
    label: "Available Supplies",
    icon: Package,
    iconColor: "text-green-600",
    iconBackground: "bg-green-50",
  },
  {
    label: "Low Stock Items",
    icon: AlertTriangle,
    iconColor: "text-orange-600",
    iconBackground: "bg-orange-50",
  },
  {
    label: "Active Shelters",
    icon: Users,
    iconColor: "text-purple-600",
    iconBackground: "bg-purple-50",
  },
];

function StatCard({ stat }) {
  const Icon = stat.icon;

  return (
    <div className="flex min-h-[178px] items-start gap-5 rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
      <div
        className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-xl ${stat.iconBackground}`}
      >
        <Icon size={26} strokeWidth={1.9} className={stat.iconColor} />
      </div>

      <div>
        <p className="mb-3 text-sm font-medium text-slate-500">
          {stat.label}
        </p>

        <h2 className="text-4xl font-bold tracking-tight text-slate-950">
          {stat.value}
        </h2>

        <p className="mt-3 text-sm text-slate-500">
          {stat.description}
        </p>
      </div>
    </div>
  );
}

function PriorityRequests({ requests, isLoading, onViewAll }) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between px-7 py-6">
        <div>
          <h2 className="text-xl font-bold text-slate-950">
            Priority Requests
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Most urgent requests first
          </p>
        </div>

        <button
          type="button"
          onClick={onViewAll}
          className="flex items-center gap-2 font-semibold text-blue-600 transition hover:text-blue-700"
        >
          View all
          <ChevronRight size={19} />
        </button>
      </div>

      <div className="w-full overflow-x-auto">
        <table className="w-full min-w-[750px] text-left">
          <thead>
            <tr className="border-y border-slate-200 bg-slate-50/70 text-xs font-semibold uppercase text-slate-500">
              <th className="w-[15%] px-6 py-5">Request</th>
              <th className="w-[35%] px-6 py-5">Shelter</th>
              <th className="w-[20%] px-6 py-5">Item</th>
              <th className="w-[15%] px-6 py-5">Quantity</th>
              <th className="w-[15%] px-6 py-5">Urgency</th>
            </tr>
          </thead>

          <tbody>
            {!isLoading && requests.length === 0 && (
              <tr>
                <td colSpan="5" className="px-6 py-8 text-center text-sm text-slate-500">
                  No open requests.
                </td>
              </tr>
            )}
            {requests.map((request) => (
              <tr
                key={request.request_id}
                className="border-b border-slate-200 last:border-b-0 transition-colors hover:bg-slate-50"
              >
                <td className="px-6 py-7 text-sm font-medium text-slate-500">
                  {`REQ-${String(request.request_id).padStart(5, "0")}`}
                </td>

                <td className="px-6 py-7 text-sm font-semibold text-slate-950">
                  {request.shelter}
                </td>

                <td className="px-6 py-7 text-sm text-slate-500">
                  {request.item_name}
                </td>

                <td className="px-6 py-7 text-sm text-slate-500">
                  {request.quantity}
                </td>

                <td className="px-6 py-7">
                  <span
                    className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ${
                      request.urgency === "Critical"
                        ? "bg-red-50 text-red-600"
                        : "bg-orange-50 text-orange-600"
                    }`}
                  >
                    {request.urgency}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function NeedsAttention({ warnings, isLoading, onReviewInventory }) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-7 py-6">
        <h2 className="text-xl font-bold text-slate-950">
          Needs Attention
        </h2>
        <p className="mt-2 text-sm text-slate-500">
          Current stock warnings
        </p>
      </div>

      <div className="px-6">
        {!isLoading && warnings.length === 0 && (
          <p className="py-6 text-sm text-slate-500">No stock warnings.</p>
        )}
        {warnings.map((warning) => (
          <div
            key={warning.warehouse_id}
            className="flex items-center justify-between gap-4 border-b border-slate-200 py-6"
          >
            <div className="flex min-w-0 items-center gap-4">
              <div
                className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${
                    warning.status === "Out Of Stock"
                    ? "bg-red-50 text-red-600"
                    : "bg-orange-50 text-orange-600"
                }`}
              >
                {warning.status === "Out Of Stock" ? (
                  <X size={23} strokeWidth={2} />
                ) : (
                  <AlertTriangle size={23} strokeWidth={2} />
                )}
              </div>

              <div>
                <h3 className="font-semibold text-slate-950">
                  {warning.item_name}
                </h3>
                <p className="mt-1 text-sm text-slate-500">
                  {warning.status === "Out Of Stock"
                    ? `Out of stock at ${warning.warehouse_code}`
                    : `Below minimum stock at ${warning.warehouse_code}`}
                </p>
              </div>
            </div>

            <span className="font-bold text-slate-950">
              {warning.quantity}
            </span>
          </div>
        ))}

        <button
          type="button"
          onClick={onReviewInventory}
          className="my-4 w-full rounded-xl border border-slate-200 bg-white px-5 py-4 font-semibold text-slate-800 transition hover:border-blue-300 hover:bg-blue-50"
        >
          Review Inventory
        </button>
      </div>
    </section>
  );
}

export default function OperationsOverview({
  onViewRequests,
  onReviewInventory,
  authenticated,
  onRequestLogin,
}) {
  const [activeModal, setActiveModal] = useState(null);
  const [requests, setRequests] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadOverview() {
      if (!authenticated) {
        setRequests([]);
        setInventory([]);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError("");
      try {
        const [requestsResponse, inventoryResponse] = await Promise.all([
          fetch("/requests", { credentials: "same-origin" }),
          fetch("/warehouse", { credentials: "same-origin" }),
        ]);
        const [requestData, inventoryData] = await Promise.all([
          requestsResponse.json(),
          inventoryResponse.json(),
        ]);
        if (!requestsResponse.ok) {
          throw new Error(requestData.error || "Unable to load requests.");
        }
        if (!inventoryResponse.ok) {
          throw new Error(inventoryData.error || "Unable to load inventory.");
        }
        if (!cancelled) {
          setRequests(requestData);
          setInventory(inventoryData);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError.message || "Unable to load the operations overview.");
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadOverview();
    return () => { cancelled = true; };
  }, [authenticated]);

  const openRequests = requests.filter((request) => request.status === "pending");
  const priorityRequests = [...openRequests]
    .sort((left, right) => {
      const urgencyOrder = { Critical: 0, High: 1, Moderate: 2 };
      return urgencyOrder[left.urgency] - urgencyOrder[right.urgency]
        || right.request_id - left.request_id;
    })
    .slice(0, 3);
  const stockWarnings = inventory.filter(
    (item) => item.status === "Low Stock" || item.status === "Out Of Stock",
  );
  const lowStockItemCount = new Set(stockWarnings.map((item) => item.item_name)).size;
  const outOfStockItemCount = new Set(
    stockWarnings
      .filter((item) => item.status === "Out Of Stock")
      .map((item) => item.item_name),
  ).size;
  const totalUnits = inventory.reduce((total, item) => total + item.quantity, 0);
  const warehouseCount = new Set(inventory.map((item) => item.warehouse_code)).size;
  const activeShelterCount = new Set(openRequests.map((request) => request.shelter)).size;
  const stats = [
    { ...statDefinitions[0], value: openRequests.length, description: `${openRequests.filter((request) => request.urgency === "Critical").length} are critical` },
    { ...statDefinitions[1], value: totalUnits.toLocaleString(), description: `Across ${warehouseCount} warehouses` },
    { ...statDefinitions[2], value: lowStockItemCount, description: `${outOfStockItemCount} out of stock` },
    { ...statDefinitions[3], value: activeShelterCount, description: "With open requests" },
  ];

  const handleViewRequests = () => {
    if (onViewRequests) {
      onViewRequests();
    } else {
      setActiveModal("requests");
    }
  };

  const handleReviewInventory = () => {
    if (onReviewInventory) {
      onReviewInventory();
    } else {
      setActiveModal("inventory");
    }
  };

  return (
    <main className="min-h-screen bg-[#f8fafc] p-4 text-slate-950 sm:p-6 lg:p-8">
      <div className="mx-auto max-w-[1920px]">
        {/* Page Header */}
        <header className="mb-9">
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Operations Overview
          </h1>

          <p className="mt-5 text-base text-slate-500 sm:text-lg">
            A simple view of current requests and available supplies.
          </p>
        </header>

        {error && <p role="alert" className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
        {!authenticated && (
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-5 py-4">
            <p className="text-sm text-slate-600">Log in to view live requests and inventory.</p>
            <button type="button" onClick={onRequestLogin} className="font-semibold text-blue-600 hover:text-blue-700">Log in</button>
          </div>
        )}

        {/* Statistics */}
        <div className="mb-7 grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {stats.map((stat) => (
            <StatCard key={stat.label} stat={stat} />
          ))}
        </div>

        {/* Dashboard Content */}
        <div className="grid grid-cols-1 items-stretch gap-7 xl:grid-cols-3">
          <div className="xl:col-span-2">
            <PriorityRequests requests={priorityRequests} isLoading={isLoading} onViewAll={handleViewRequests} />
          </div>

          <div className="xl:col-span-1">
            <NeedsAttention warnings={stockWarnings} isLoading={isLoading} onReviewInventory={handleReviewInventory} />
          </div>
        </div>
      </div>

      {/* Fallback modal when no navigation callbacks are provided */}
      {activeModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setActiveModal(null);
            }
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label={
              activeModal === "requests"
                ? "Priority Requests"
                : "Inventory Warnings"
            }
            className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-xl"
          >
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-xl font-bold">
                {activeModal === "requests"
                  ? "Priority Requests"
                  : "Inventory Warnings"}
              </h2>
              <button
                type="button"
                aria-label="Close"
                onClick={() => setActiveModal(null)}
                className="rounded-lg p-2 hover:bg-slate-100"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-3">
              {activeModal === "requests"
                    ? priorityRequests.map((request) => (
                    <div
                      key={request.request_id}
                      className="rounded-xl border border-slate-200 p-4"
                    >
                      <div className="flex justify-between gap-3">
                        <span className="font-semibold">
                          {`REQ-${String(request.request_id).padStart(5, "0")}`}
                        </span>
                        <span className="text-sm text-red-600">
                          {request.urgency}
                        </span>
                      </div>
                      <p className="mt-2 text-sm">
                        {request.shelter}
                      </p>
                      <p className="mt-1 text-sm text-slate-500">
                        {request.item_name} — {request.quantity} units
                      </p>
                    </div>
                  ))
                    : stockWarnings.map((warning) => (
                    <div
                      key={warning.warehouse_id}
                      className="rounded-xl border border-slate-200 p-4"
                    >
                      <div className="flex justify-between gap-3">
                        <span className="font-semibold">
                          {warning.item_name}
                        </span>
                        <span className="font-bold">
                          {warning.quantity}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-slate-500">
                        {warning.status === "Out Of Stock"
                          ? `Out of stock at ${warning.warehouse_code}`
                          : `Below minimum stock at ${warning.warehouse_code}`}
                      </p>
                    </div>
                  ))}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
