import os
import httpx
import asyncio
import sys
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

# 1. Load environment variables from .env file
load_dotenv()

# Get the API base URL from the environment
API_BASE_URL = os.environ.get("API_BASE_URL")

if not API_BASE_URL:
    print("FATAL: API_BASE_URL environment variable is not set.")
    print("Please create a .env file or set the variable in your environment.")
    exit(1)

# Initialize FastMCP Server
mcp = FastMCP("MyCoco MCP Server")

# --- API Client for Backend Communication ---

class ApiClient:
    """
    A robust, reusable client for interacting with the backend API.
    Uses httpx.AsyncClient for asynchronous requests.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url
        # Use an AsyncClient to manage connections efficiently
        # INCREASED TIMEOUT TO 60.0 SECONDS FOR FREE-TIER HOSTING
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0) 
        print(f"✅ API Client initialized with Base URL: {self.base_url}")

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Helper to make an async request and handle standard API response format."""
        # Note: The implementation manually prepends the base URL for the request
        url = self.base_url + path
        try:
            # Determine the data being sent for logging purposes
            # For GET, we log params; for POST/others, we log the JSON payload
            request_data = kwargs.get('params', kwargs.get('json', 'N/A'))
            print(f"🚀 Calling {method} {path} with data: {request_data}")
            
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status() # Raise exception for 4xx/5xx status codes
            
            # Assuming your backend returns JSON with { "success": true, "data": [...] }
            data = response.json()
            if not data.get('success'):
                error_msg = data.get('error', "API call failed with no specific error message.")
                # Uses the imported or fallback ToolCallError
                raise ToolCallError(f"Backend reported failure for {path}: {error_msg}")

            return data.get('data', [])

        except httpx.HTTPStatusError as e:
            # Handle specific HTTP errors (404, 500, etc.)
            error_details = f"HTTP Error {e.response.status_code}: {e.response.text}"
            print(f"❌ {error_details}")
            raise ToolCallError(f"Failed to fetch data from {path}. {error_details}")
        except httpx.RequestError as e:
            # Handle network/connection errors
            print(f"❌ Request Error: {e}")
            raise ToolCallError(f"Network error accessing {url}. Check API server status. Details: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            raise ToolCallError(f"An unexpected error occurred during API call. Details: {e}")

    async def get(self, path: str, params: dict = None) -> dict:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, data: dict) -> dict:
        """Helper for making POST requests with JSON payload."""
        # httpx uses 'json' keyword to automatically serialize the dict payload
        return await self._request("POST", path, json=data)


# --- FastMCP Tools Implementation ---

class McpDataTools:
    """
    Contains all FastMCP tools for data retrieval and creation.
    """
    def __init__(self, client: ApiClient):
        self.client = client

    # Helper function to create the params dict for GET requests, skipping 'self' and None values
    def _collect_params(self, local_vars: dict) -> dict:
        """Collects function arguments into a dictionary suitable for API params."""
        # We also filter out any default values that might be present but are None
        return {k: v for k, v in local_vars.items() if k != 'self' and v is not None}

    # ------- The GET/Fetching section ----

    # --- USERS TOOLS ---

    @mcp.tool(
        description="Fetch a list of users, optionally filtered by role, region, area, status, company ID, or a search term (email)."
    )
    async def get_users_list(
        self, 
        search: Annotated[str | None, "Search term for user (e.g., part of an email)."] = None,
        limit: Annotated[int, Field(description="Maximum number of records to return (default 50).", default=50)] = 50,
        role: Annotated[str | None, "Filter users by role."] = None,
        region: Annotated[str | None, "Filter users by region."] = None,
        area: Annotated[str | None, "Filter users by area."] = None,
        status: Annotated[str | None, "Filter users by status."] = None,
        companyId: Annotated[int | None, "Filter users belonging to a specific company ID."] = None,
    ) -> list[dict]:
        """Maps to: GET /api/users"""
        params = self._collect_params(locals())
        return await self.client.get("/api/users", params=params)

    @mcp.tool(
        description="Fetch a single user's detailed information using their unique ID."
    )
    async def get_user_by_id(
        self, 
        user_id: Annotated[int, "The unique ID of the user to fetch."],
    ) -> dict:
        """Maps to: GET /api/users/{id}"""
        return await self.client.get(f"/api/users/{user_id}")

    # --- DEALERS TOOLS ---

    @mcp.tool(
        description="Fetch a list of dealers, optionally filtered by region, area, type, or the user (salesman) ID responsible for the dealer."
    )
    async def get_dealers_list(
        self, 
        limit: Annotated[int, Field(description="Maximum number of records to return (default 50).", default=50)] = 50,
        region: Annotated[str | None, "Filter dealers by region."] = None,
        area: Annotated[str | None, "Filter dealers by area."] = None,
        type: Annotated[str | None, "Filter dealers by type."] = None,
        userId: Annotated[int | None, "Filter dealers managed by a specific user ID."] = None,
    ) -> list[dict]:
        """Maps to: GET /api/dealers"""
        params = self._collect_params(locals())
        return await self.client.get("/api/dealers", params=params)

    @mcp.tool(
        description="Fetch a single dealer's detailed information using their unique ID."
    )
    async def get_dealer_by_id(
        self, 
        dealer_id: Annotated[int, "The unique ID of the dealer to fetch."],
    ) -> dict:
        """Maps to: GET /api/dealers/{id}"""
        return await self.client.get(f"/api/dealers/{dealer_id}")


    # --- DVR (Daily Visit Reports) TOOLS ---

    @mcp.tool(
        description="Fetch Daily Visit Reports, supporting date range filtering (startDate, endDate) and filtering by user ID, dealer type, or visit type."
    )
    async def get_dvr_reports(
        self, 
        startDate: Annotated[str | None, "Start date for filtering (e.g., 'YYYY-MM-DD')."] = None,
        endDate: Annotated[str | None, "End date for filtering (e.g., 'YYYY-MM-DD')."] = None,
        limit: Annotated[int, Field(description="Maximum number of records to return (default 50).", default=50)] = 50,
        userId: Annotated[int | None, "Filter reports by the user ID who submitted them."] = None,
        dealerType: Annotated[str | None, "Filter reports by the type of dealer visited."] = None,
        visitType: Annotated[str | None, "Filter reports by the type of visit conducted."] = None,
    ) -> list[dict]:
        """Maps to: GET /api/daily-visit-reports"""
        params = self._collect_params(locals())
        return await self.client.get("/api/daily-visit-reports", params=params)

    @mcp.tool(
        description="Fetch a single Daily Visit Report using its unique ID."
    )
    async def get_dvr_report_by_id(
        self, 
        report_id: Annotated[int, "The unique ID of the DVR to fetch."],
    ) -> dict:
        """Maps to: GET /api/daily-visit-reports/{id}"""
        return await self.client.get(f"/api/daily-visit-reports/{report_id}")
    
    # --- TVR (Technical Visit Reports) TOOLS ---

    @mcp.tool(
        description="Fetch Technical Visit Reports, supporting date range filtering (startDate, endDate) and filtering by user ID, visit type, or service type."
    )
    async def get_tvr_reports(
        self, 
        startDate: Annotated[str | None, "Start date for filtering (e.g., 'YYYY-MM-DD')."] = None,
        endDate: Annotated[str | None, "End date for filtering (e.g., 'YYYY-MM-DD')."] = None,
        limit: Annotated[int, Field(description="Maximum number of records to return (default 50).", default=50)] = 50,
        userId: Annotated[int | None, "Filter reports by the user ID who submitted them."] = None,
        visitType: Annotated[str | None, "Filter reports by the type of visit conducted (e.g., 'Installation', 'Maintenance')."] = None,
        serviceType: Annotated[str | None, "Filter reports by the service type performed (e.g., 'Warranty', 'Paid Service')."] = None,
    ) -> list[dict]:
        """Maps to: GET /api/technical-visit-reports"""
        params = self._collect_params(locals())
        return await self.client.get("/api/technical-visit-reports", params=params)

    @mcp.tool(
        description="Fetch a single Technical Visit Report using its unique ID."
    )
    async def get_tvr_report_by_id(
        self, 
        report_id: Annotated[int, "The unique ID of the TVR to fetch."],
    ) -> dict:
        """Maps to: GET /api/technical-visit-reports/{id}"""
        return await self.client.get(f"/api/technical-visit-reports/{report_id}")
        
    # --- SALES ORDERS TOOLS ---

    @mcp.tool(
        description="Fetch Sales Orders, supporting date range filtering (startDate, endDate) based on estimated delivery date, and filtering by salesman ID or dealer ID."
    )
    async def get_sales_orders(
        self, 
        startDate: Annotated[str | None, "Start date for filtering estimated delivery (e.g., 'YYYY-MM-DD')."] = None,
        endDate: Annotated[str | None, "End date for filtering estimated delivery (e.g., 'YYYY-MM-DD')."] = None,
        limit: Annotated[int, Field(description="Maximum number of records to return (default 50).", default=50)] = 50,
        salesmanId: Annotated[int | None, "Filter orders by the unique ID of the salesman who booked the order."] = None,
        dealerId: Annotated[str | None, "Filter orders by the ID of the dealer who placed the order."] = None,
    ) -> list[dict]:
        """Maps to: GET /api/sales-orders"""
        params = self._collect_params(locals())
        return await self.client.get("/api/sales-orders", params=params)

    @mcp.tool(
        description="Fetch a single Sales Order's detailed information using its unique ID."
    )
    async def get_sales_order_by_id(
        self, 
        order_id: Annotated[int, "The unique ID of the Sales Order to fetch."],
    ) -> dict:
        """Maps to: GET /api/sales-orders/{id}"""
        return await self.client.get(f"/api/sales-orders/{order_id}")

    #----- End of GET Section

    # ------- The POST/Creation section ----

    @mcp.tool(
        description="Create a new Sales Order record. The tool returns the created Sales Order record, including its new ID. Requires salesmanId, dealerId, quantity, unit, and payment details.",
    )
    async def post_sales_order(
        self, 
        salesmanId: Annotated[int, "The ID of the salesman who booked the order (required)."],
        dealerId: Annotated[str, "The ID of the dealer who placed the order (required)."],
        quantity: Annotated[float, "Order quantity (e.g., 10.5)."],
        unit: Annotated[str, "The unit of the quantity (e.g., 'MT', 'Liters') (required)."],
        orderTotal: Annotated[float, "Total value of the order (required)."],
        advancePayment: Annotated[float, "Advance payment made (required)."],
        pendingPayment: Annotated[float, "Pending payment amount (required)."],
        estimatedDelivery: Annotated[str, "The estimated delivery date (YYYY-MM-DD format) (required)."],
        remarks: Annotated[str | None, "Optional remarks about the order."] = None,
    ) -> dict:
        """
        Creates a new Sales Order.
        Maps to: POST /api/sales-orders
        """
        # Collect all parameters for the POST body
        data = self._collect_params(locals())
        return await self.client.post("/api/sales-orders", data=data)

    @mcp.tool(
        description="Create a new Daily Visit Report (DVR). The tool returns the created report record, including its new ID. Requires detailed information about the visit, including user, location, metrics, and products.",
    )
    async def post_dvr_report(
        self, 
        userId: Annotated[int, "The unique ID of the user who submitted the report (required)."],
        reportDate: Annotated[str, "Date of the report (YYYY-MM-DD format) (required)."],
        dealerType: Annotated[str, "Type of dealer visited (required)."],
        location: Annotated[str, "Location details of the visit (required)."],
        latitude: Annotated[float, "Geographical latitude of the visit (required)."],
        longitude: Annotated[float, "Geographical longitude of the visit (required)."],
        visitType: Annotated[str, "Type of visit conducted (required)."],
        dealerTotalPotential: Annotated[float, "Total potential of the dealer in volume/value (required)."],
        dealerBestPotential: Annotated[float, "Best case potential of the dealer in volume/value (required)."],
        brandSelling: Annotated[list[str], "List of brands the dealer is selling (required)."],
        todayOrderMt: Annotated[float, "Order booked today in metric tons (required)."],
        todayCollectionRupees: Annotated[float, "Collection amount in rupees today (required)."],
        feedbacks: Annotated[str, "Key feedback or issues from the visit (required)."],
        checkInTime: Annotated[str, "Visit check-in timestamp (ISO 8601 string or date string) (required)."],
        
        dealerName: Annotated[str | None, "Optional name of the dealer."] = None,
        subDealerName: Annotated[str | None, "Optional name of the sub-dealer."] = None,
        contactPerson: Annotated[str | None, "Optional contact person name."] = None,
        contactPersonPhoneNo: Annotated[str | None, "Optional contact person phone number."] = None,
        overdueAmount: Annotated[float | None, "Optional overdue amount."] = None,
        solutionBySalesperson: Annotated[str | None, "Optional solution provided by the salesperson."] = None,
        anyRemarks: Annotated[str | None, "Optional additional remarks."] = None,
        checkOutTime: Annotated[str | None, "Optional visit check-out timestamp."] = None,
        inTimeImageUrl: Annotated[str | None, "Optional URL for the check-in photo."] = None,
        outTimeImageUrl: Annotated[str | None, "Optional URL for the check-out photo."] = None,
    ) -> dict:
        """
        Creates a new Daily Visit Report.
        Maps to: POST /api/daily-visit-reports
        """
        # Collect all parameters for the POST body
        data = self._collect_params(locals())

        # Note: We rely on FastMCP's schema generation to enforce 'brandSelling' is a list of strings.
        # If the LLM somehow provides a single string, FastMCP/Pydantic validation should handle it.
            
        return await self.client.post("/api/daily-visit-reports", data=data)

    @mcp.tool(
        description="Create a new Technical Visit Report (TVR). The tool returns the created report record, including its new ID. Requires detailed information about the technical site visit, client feedback, and conversion details.",
    )
    async def post_tvr_report(
        self, 
        userId: Annotated[int, "The unique ID of the user who submitted the report (required)."],
        reportDate: Annotated[str, "Date of the report (YYYY-MM-DD format) (required)."],
        visitType: Annotated[str, "Type of visit conducted (required)."],
        siteNameConcernedPerson: Annotated[str, "Name of the site or concerned person (required)."],
        phoneNo: Annotated[str, "Contact phone number (required)."],
        clientsRemarks: Annotated[str, "Remarks or feedback from the client (required)."],
        dealerName: Annotated[str, "Name of the related dealer (required)."],
        conversionStatus: Annotated[str, "Status of conversion for the client/site (e.g., 'Converted', 'Follow-up') (required)."],
        conversionVolume: Annotated[float, "Estimated volume of conversion in metric tons (required)."],
        
        # Optional fields
        dealerId: Annotated[str | None, "Optional ID of the related dealer."] = None,
        serviceType: Annotated[str | None, "Optional service type performed (e.g., 'Warranty', 'Paid Service')."] = None,
        competitorsProduct: Annotated[str | None, "Optional product from competitors found at the site."] = None,
        latitude: Annotated[float | None, "Optional Geographical latitude of the visit."] = None,
        longitude: Annotated[float | None, "Optional Geographical longitude of the visit."] = None,
        inTimeImageUrl: Annotated[str | None, "Optional URL for the check-in photo."] = None,
        outTimeImageUrl: Annotated[str | None, "Optional URL for the check-out photo."] = None,
    ) -> dict:
        """
        Creates a new Technical Visit Report.
        Maps to: POST /api/technical-visit-reports
        """
        # Collect all parameters for the POST body
        data = self._collect_params(locals())
        return await self.client.post("/api/technical-visit-reports", data=data)

# --- Main Execution ---
def main():
    # init your API client and register tools
    api_client = ApiClient(API_BASE_URL)
    McpDataTools(api_client)

    print("\nStarting MyCoco MCP Server...")
    print("Server is ready to serve all registered tools.")

    # DO NOT await this. It manages the loop itself.
    mcp.run(transport="http", port=8000)  # or stdio if you prefer

if __name__ == "__main__":
    main()
