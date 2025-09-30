import os
import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP 
from typing import Annotated # Required for adding metadata to types
from pydantic import Field # Required for defining parameter descriptions and constraints
try:
    # The canonical import path for FastMCP
    from fastmcp import ToolCallError
except ImportError:
    # Fallback: Define a placeholder class if ToolCallError is not directly exported.
    class ToolCallError(Exception):
        """A placeholder for the missing ToolCallError from fastmcp."""
        pass

# --- Configuration & Initialization ---
load_dotenv()
API_BASE_URL = os.environ.get("API_BASE_URL", "https://myserverbymycoco.onrender.com")

if not API_BASE_URL:
    print("FATAL: API_BASE_URL environment variable is not set.")
    exit(1)

mcp = FastMCP("MyCoco MCP Server")

# --- API Client for Backend Communication ---

class ApiClient:
    def __init__(self, base_url: str):
        self.client = httpx.AsyncClient(base_url=base_url, timeout=60.0) 
        print(f"✅ API Client initialized with Base URL: {base_url}")

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        url = self.client.base_url.join(path)
        try:
            request_data = kwargs.get('params', kwargs.get('json', 'N/A'))
            print(f"🚀 Calling {method} {url} with data: {request_data}")
            
            headers = kwargs.pop("headers", {})
            headers = {"Accept": "application/json", **headers}

            response = await self.client.request(method, path, headers=headers, **kwargs)
            response.raise_for_status()

            content_type = (response.headers.get("content-type") or "").lower()
            if "application/json" in content_type:
                data = response.json()
                if isinstance(data, dict) and "success" in data:
                    if not data.get('success'):
                        error_msg = data.get('error', "API call failed.")
                        raise ToolCallError(f"Backend reported failure for {path}: {error_msg}")
                    return data.get('data', [])
                return data
            return response.content
        except httpx.HTTPStatusError as e:
            error_details = f"HTTP Error {e.response.status_code}: {e.response.text}"
            print(f"❌ {error_details}")
            raise ToolCallError(f"Failed to fetch data from {path}. {error_details}")
        except httpx.RequestError as e:
            print(f"❌ Request Error: {e}")
            raise ToolCallError(f"Network error accessing {url}. Details: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            raise ToolCallError(f"An unexpected error occurred. Details: {e}")

    async def get(self, path: str, params: dict = None) -> dict:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, data: dict) -> dict:
        return await self._request("POST", path, json=data)

# --- Tool Implementation Class (No Decorators Here) ---
# This class holds all the logic but does not define the public-facing tools.

class McpDataToolsImpl:
    def __init__(self, client: ApiClient):
        self.client = client

    def _collect_params(self, local_vars: dict) -> dict:
        return {k: v for k, v in local_vars.items() if v is not None}

    async def get_users_list(self, **kwargs) -> list[dict]:
        params = self._collect_params(kwargs)
        return await self.client.get("/api/users", params=params)

    async def get_user_by_id(self, *, user_id: int) -> dict:
        return await self.client.get(f"/api/users/{user_id}")

    async def get_dealers_list(self, **kwargs) -> list[dict]:
        params = self._collect_params(kwargs)
        return await self.client.get("/api/dealers", params=params)

    async def get_dealer_by_id(self, *, dealer_id: str) -> dict:
        return await self.client.get(f"/api/dealers/{dealer_id}")

    async def get_dvr_reports(self, **kwargs) -> list[dict]:
        params = self._collect_params(kwargs)
        return await self.client.get("/api/daily-visit-reports", params=params)

    async def get_dvr_report_by_id(self, *, report_id: str) -> dict:
        return await self.client.get(f"/api/daily-visit-reports/{report_id}")

    async def get_tvr_reports(self, **kwargs) -> list[dict]:
        params = self._collect_params(kwargs)
        return await self.client.get("/api/technical-visit-reports", params=params)

    async def get_tvr_report_by_id(self, *, report_id: str) -> dict:
        return await self.client.get(f"/api/technical-visit-reports/{report_id}")

    async def get_sales_orders(self, **kwargs) -> list[dict]:
        params = self._collect_params(kwargs)
        return await self.client.get("/api/sales-orders", params=params)

    async def get_sales_order_by_id(self, *, order_id: str) -> dict:
        return await self.client.get(f"/api/sales-orders/{order_id}")

    async def post_sales_order(self, **kwargs) -> dict:
        return await self.client.post("/api/sales-orders", data=kwargs)

    async def post_dvr_report(self, **kwargs) -> dict:
        return await self.client.post("/api/daily-visit-reports", data=kwargs)

    async def post_tvr_report(self, **kwargs) -> dict:
        return await self.client.post("/api/technical-visit-reports", data=kwargs)


# --- Global Instances ---
# We create one instance of the client and the implementation class to be used by the blueprint functions.
api_client = ApiClient(API_BASE_URL)
tools_impl = McpDataToolsImpl(api_client)


# --- Tool Blueprints (Decorated Functions for the AI) ---
# These have clean signatures (no `self`) and define the schema for the AI. They call the implementation class.

@mcp.tool(description="Fetch a list of users.", annotations={"readOnlyHint": True})
async def get_users_list(
    search: Annotated[str | None, "Search term for user (e.g., email)."] = None,
    limit: Annotated[int, Field(description="Max records (default 50).", default=50)] = 50,
    role: Annotated[str | None, "Filter by role."] = None, region: Annotated[str | None, "Filter by region."] = None,
    area: Annotated[str | None, "Filter by area."] = None, status: Annotated[str | None, "Filter by status."] = None,
    companyId: Annotated[int | None, "Filter by company ID."] = None
) -> list[dict]:
    return await tools_impl.get_users_list(**locals())

@mcp.tool(description="Fetch a user by their unique ID.", annotations={"readOnlyHint": True})
async def get_user_by_id(user_id: Annotated[int, "The unique ID of the user."]) -> dict:
    return await tools_impl.get_user_by_id(user_id=user_id)

@mcp.tool(description="Fetch a list of dealers.", annotations={"readOnlyHint": True})
async def get_dealers_list(
    limit: Annotated[int, Field(description="Max records (default 50).", default=50)] = 50,
    region: Annotated[str | None, "Filter by region."] = None, area: Annotated[str | None, "Filter by area."] = None,
    type: Annotated[str | None, "Filter by type."] = None, userId: Annotated[int | None, "Filter by user ID."] = None
) -> list[dict]:
    return await tools_impl.get_dealers_list(**locals())

@mcp.tool(description="Fetch a dealer by their unique ID.", annotations={"readOnlyHint": True})
async def get_dealer_by_id(dealer_id: Annotated[str, "The unique ID of the dealer."]) -> dict:
    return await tools_impl.get_dealer_by_id(dealer_id=dealer_id)

@mcp.tool(description="Fetch Daily Visit Reports (DVRs).", annotations={"readOnlyHint": True})
async def get_dvr_reports(
    startDate: Annotated[str | None, "Start date (YYYY-MM-DD)."] = None,
    endDate: Annotated[str | None, "End date (YYYY-MM-DD)."] = None,
    limit: Annotated[int, Field(description="Max records (default 50).", default=50)] = 50,
    userId: Annotated[int | None, "Filter by user ID."] = None, dealerType: Annotated[str | None, "Filter by dealer type."] = None,
    visitType: Annotated[str | None, "Filter by visit type."] = None
) -> list[dict]:
    return await tools_impl.get_dvr_reports(**locals())

@mcp.tool(description="Fetch a Daily Visit Report (DVR) by its ID.", annotations={"readOnlyHint": True})
async def get_dvr_report_by_id(report_id: Annotated[str, "The unique ID of the report."]) -> dict:
    return await tools_impl.get_dvr_report_by_id(report_id=report_id)

@mcp.tool(description="Fetch Technical Visit Reports (TVRs).", annotations={"readOnlyHint": True})
async def get_tvr_reports(
    startDate: Annotated[str | None, "Start date (YYYY-MM-DD)."] = None,
    endDate: Annotated[str | None, "End date (YYYY-MM-DD)."] = None,
    limit: Annotated[int, Field(description="Max records (default 50).", default=50)] = 50,
    userId: Annotated[int | None, "Filter by user ID."] = None,
    visitType: Annotated[str | None, "Filter by visit type."] = None,
    serviceType: Annotated[str | None, "Filter by service type."] = None
) -> list[dict]:
    return await tools_impl.get_tvr_reports(**locals())

@mcp.tool(description="Fetch a Technical Visit Report (TVR) by its ID.", annotations={"readOnlyHint": True})
async def get_tvr_report_by_id(report_id: Annotated[str, "The unique ID of the report."]) -> dict:
    return await tools_impl.get_tvr_report_by_id(report_id=report_id)

@mcp.tool(description="Fetch Sales Orders.", annotations={"readOnlyHint": True})
async def get_sales_orders(
    startDate: Annotated[str | None, "Start date for delivery (YYYY-MM-DD)."] = None,
    endDate: Annotated[str | None, "End date for delivery (YYYY-MM-DD)."] = None,
    limit: Annotated[int, Field(description="Max records (default 50).", default=50)] = 50,
    salesmanId: Annotated[int | None, "Filter by salesman ID."] = None,
    dealerId: Annotated[str | None, "Filter by dealer ID."] = None
) -> list[dict]:
    return await tools_impl.get_sales_orders(**locals())

@mcp.tool(description="Fetch a Sales Order by its ID.", annotations={"readOnlyHint": True})
async def get_sales_order_by_id(order_id: Annotated[str, "The unique ID of the order."]) -> dict:
    return await tools_impl.get_sales_order_by_id(order_id=order_id)

@mcp.tool(
    description="Create a new Sales Order.",
    annotations={"destructiveHint": True, "requiresConfirmation": True},
)
async def post_sales_order(
    salesmanId: Annotated[int, "The salesman's ID."], dealerId: Annotated[str, "The dealer's ID."],
    quantity: Annotated[float, "Order quantity."], unit: Annotated[str, "Unit of quantity (e.g., 'MT')."],
    orderTotal: Annotated[float, "Total value of the order."],
    advancePayment: Annotated[float, "Advance payment made."],
    pendingPayment: Annotated[float, "Pending payment amount."],
    estimatedDelivery: Annotated[str, "Estimated delivery date (YYYY-MM-DD)."],
    remarks: Annotated[str | None, "Optional remarks."] = None,
) -> dict:
     # --- FIX: Type conversion and data collection moved here for consistency with other POST tools ---
    data = tools_impl._collect_params(locals())

    # CRITICAL FIX: Convert float arguments to strings to satisfy the backend API schema (numeric fields)
    if 'quantity' in data: data['quantity'] = str(data['quantity'])
    if 'orderTotal' in data: data['orderTotal'] = str(data['orderTotal'])
    if 'advancePayment' in data: data['advancePayment'] = str(data['advancePayment'])
    if 'pendingPayment' in data: data['pendingPayment'] = str(data['pendingPayment'])

    # Now send the corrected data payload
    return await tools_impl.client.post("/api/sales-orders", data=data)

@mcp.tool(
    description="Create a new Daily Visit Report (DVR).",
    annotations={"destructiveHint": True, "requiresConfirmation": True},
)
async def post_dvr_report(
    userId: Annotated[int, "The user's ID."], reportDate: Annotated[str, "Date of the report (YYYY-MM-DD)."],
    dealerType: Annotated[str, "Type of dealer."], location: Annotated[str, "Location of the visit."],
    latitude: Annotated[float, "Geographical latitude."], longitude: Annotated[float, "Geographical longitude."],
    visitType: Annotated[str, "Type of visit."], dealerTotalPotential: Annotated[float, "Dealer's total potential."],
    dealerBestPotential: Annotated[float, "Dealer's best potential."],
    brandSelling: Annotated[list[str], "List of brands the dealer sells."],
    todayOrderMt: Annotated[float, "Order today (in MT)."],
    todayCollectionRupees: Annotated[float, "Collection today (in Rupees)."],
    feedbacks: Annotated[str, "Feedback from the visit."], checkInTime: Annotated[str, "Check-in timestamp."],
    dealerName: Annotated[str | None, "Dealer's name."] = None,
    subDealerName: Annotated[str | None, "Sub-dealer's name."] = None,
    contactPerson: Annotated[str | None, "Contact person's name."] = None,
    contactPersonPhoneNo: Annotated[str | None, "Contact person's phone."] = None,
    overdueAmount: Annotated[float | None, "Overdue amount."] = None,
    solutionBySalesperson: Annotated[str | None, "Solution provided."] = None,
    anyRemarks: Annotated[str | None, "Other remarks."] = None,
    checkOutTime: Annotated[str | None, "Check-out timestamp."] = None,
    inTimeImageUrl: Annotated[str | None, "Check-in image URL."] = None,
    outTimeImageUrl: Annotated[str | None, "Check-out image URL."] = None
) -> dict:
    # --- FIX: Convert float arguments to strings for DVR POST request ---
    data = tools_impl._collect_params(locals())
    if 'dealerTotalPotential' in data: data['dealerTotalPotential'] = str(data['dealerTotalPotential'])
    if 'dealerBestPotential' in data: data['dealerBestPotential'] = str(data['dealerBestPotential'])
    if 'todayOrderMt' in data: data['todayOrderMt'] = str(data['todayOrderMt'])
    if 'todayCollectionRupees' in data: data['todayCollectionRupees'] = str(data['todayCollectionRupees'])
    if 'overdueAmount' in data: data['overdueAmount'] = str(data['overdueAmount'])
    # CRITICAL FIX: Add string conversion for latitude and longitude for consistency with numeric fields
    if 'latitude' in data: data['latitude'] = str(data['latitude'])
    if 'longitude' in data: data['longitude'] = str(data['longitude'])
    return await tools_impl.client.post("/api/daily-visit-reports", data=data)

@mcp.tool(
    description="Create a new Technical Visit Report (TVR).",
    annotations={"destructiveHint": True, "requiresConfirmation": True},
)
async def post_tvr_report(
    userId: Annotated[int, "The user's ID."], 
    reportDate: Annotated[str, "Date of the report (YYYY-MM-DD)."],
    visitType: Annotated[str, "Type of visit."],
    siteNameConcernedPerson: Annotated[str, "Name of the site or person."],
    phoneNo: Annotated[str, "Contact phone number."], 
    clientsRemarks: Annotated[str, "Client's remarks."],
    salespersonRemarks: Annotated[str, "Remarks provided by the salesperson."], # ADDED (Mandatory, from schema)
    siteVisitBrandInUse: Annotated[list[str], "List of brands used at the site (e.g., ['BrandX', 'BrandY'])."], # ADDED (Mandatory Array, from schema)
    influencerType: Annotated[list[str], "List of influencer types (e.g., ['Engineer', 'Owner'])."], # ADDED (Mandatory Array, from schema)
    checkInTime: Annotated[str, "Check-in timestamp."], # Check-in time is required in the DB
    
    # Corrected and Added Optional Fields to align with Zod schema:
    emailId: Annotated[str | None, "Contact email address (if available)."] = None,
    siteVisitStage: Annotated[str | None, "Stage of the site visit (e.g., 'Initial', 'Closing')."] = None,
    conversionFromBrand: Annotated[str | None, "Brand converting from (if applicable)."] = None,
    conversionQuantityValue: Annotated[float | None, "Estimated conversion volume (in MT)."] = None, # RENAMED from conversionVolume
    conversionQuantityUnit: Annotated[str | None, "Unit for conversion volume (e.g., 'MT')."] = None,
    associatedPartyName: Annotated[str | None, "Associated party name."] = None,
    serviceType: Annotated[str | None, "Service type performed."] = None,
    qualityComplaint: Annotated[str | None, "Details of any quality complaint."] = None,
    promotionalActivity: Annotated[str | None, "Details of any promotional activity."] = None,
    channelPartnerVisit: Annotated[str | None, "Details of any channel partner visit."] = None,

    # Existing Optional Fields:
    checkOutTime: Annotated[str | None, "Check-out timestamp."] = None,
    inTimeImageUrl: Annotated[str | None, "Check-in image URL."] = None,
    outTimeImageUrl: Annotated[str | None, "Check-out image URL."] = None,
) -> dict:
    # --- FIX: Convert float arguments to strings for TVR POST request ---
    data = tools_impl._collect_params(locals())
    
    # CRITICAL FIX: Convert the renamed numeric field to string. Removed latitude/longitude conversions.
    if 'conversionQuantityValue' in data and data['conversionQuantityValue'] is not None: 
        data['conversionQuantityValue'] = str(data['conversionQuantityValue'])
        
    # NOTE: The TVR Zod schema does not contain latitude/longitude. They were removed from the tool.
    
    return await tools_impl.client.post("/api/technical-visit-reports", data=data)

# --- Server Start ---
def main():
    print("\nStarting MyCoco MCP Server...")
    print("Server is ready to serve all registered tools.")
    mcp.run(transport="http", port=8000)

if __name__ == "__main__":
    main()
