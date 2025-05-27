from flask import Blueprint, request, jsonify
from services.timing import TimingControl

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/timing/enable', methods=['POST'])
def enable_timing():
    """启用计时日志"""
    TimingControl.enable()
    return jsonify({'message': 'Timing logs enabled', 'status': 'enabled'}), 200

@admin_bp.route('/admin/timing/disable', methods=['POST'])
def disable_timing():
    """禁用计时日志"""
    TimingControl.disable()
    return jsonify({'message': 'Timing logs disabled', 'status': 'disabled'}), 200

@admin_bp.route('/admin/timing/toggle', methods=['POST'])
def toggle_timing():
    """切换计时日志状态"""
    TimingControl.toggle()
    status = 'enabled' if TimingControl.status() else 'disabled'
    return jsonify({'message': f'Timing logs {status}', 'status': status}), 200

@admin_bp.route('/admin/timing/status', methods=['GET'])
def timing_status():
    """获取计时日志状态"""
    status = 'enabled' if TimingControl.status() else 'disabled'
    return jsonify({'status': status}), 200 