from flask import Blueprint, jsonify, request

from backend.database.repository import (
    dashboard_stats,
    delete_analysis,
    get_analysis,
    list_analyses,
)

history = Blueprint("history", __name__, url_prefix="/api")


@history.get("/dashboard/stats")
def get_dashboard_stats():
    return jsonify(dashboard_stats())


@history.get("/history")
def get_history():
    try:
        limit = int(request.args.get("limit", "100"))
    except ValueError:
        return jsonify({"error": {"code": "invalid_limit", "message": "Limit must be an integer."}}), 400
    if limit < 1 or limit > 200:
        return jsonify({"error": {"code": "invalid_limit", "message": "Limit must be between 1 and 200."}}), 400
    return jsonify({"analyses": list_analyses(limit)})


@history.get("/history/<analysis_id>")
def get_history_item(analysis_id: str):
    analysis = get_analysis(analysis_id)
    if analysis is None:
        return jsonify({"error": {"code": "not_found", "message": "Analysis record was not found."}}), 404
    return jsonify(analysis)


@history.delete("/history/<analysis_id>")
def delete_history_item(analysis_id: str):
    if not delete_analysis(analysis_id):
        return jsonify({"error": {"code": "not_found", "message": "Analysis record was not found."}}), 404
    return jsonify({"deleted": True, "analysis_id": analysis_id})
