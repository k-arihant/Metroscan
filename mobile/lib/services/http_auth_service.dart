import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/constants/api_constants.dart';
import '../models/user_profile.dart';
import '../models/user_role.dart';
import 'auth_service.dart';

class HttpAuthService implements AuthService {
  UserProfile? _currentUser;
  String? _token;

  String? get token => _token;

  @override
  Future<UserProfile?> getCurrentUser() async {
    if (_currentUser != null) return _currentUser;

    if (_token != null) {
      try {
        final res = await http.get(
          Uri.parse(ApiConstants.meUrl),
          headers: {'Authorization': 'Bearer $_token'},
        ).timeout(const Duration(seconds: 4));

        if (res.statusCode == 200) {
          final data = jsonDecode(res.body) as Map<String, dynamic>;
          if (data['authenticated'] == true) {
            _currentUser = UserProfile.fromJson(data);
            return _currentUser;
          }
        }
      } catch (_) {
        // Fallback silently if offline
      }
    }
    return _currentUser;
  }

  @override
  Future<UserProfile> login({
    required String email,
    required String password,
  }) async {
    try {
      final res = await http.post(
        Uri.parse(ApiConstants.loginUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email.trim(), 'password': password}),
      ).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as Map<String, dynamic>;
        _token = data['access_token'] as String?;
        _currentUser = UserProfile.fromJson(data);
        return _currentUser!;
      } else {
        final data = jsonDecode(res.body) as Map<String, dynamic>?;
        final msg = data?['detail'] ?? 'Authentication failed (${res.statusCode})';
        throw Exception(msg);
      }
    } catch (e) {
      if (e is Exception && !e.toString().contains('ClientException') && !e.toString().contains('SocketException')) {
        rethrow;
      }
      throw Exception('Could not connect to MetroScan server at ${ApiConstants.baseUrl}. Please ensure backend is running.');
    }
  }

  @override
  Future<UserProfile> loginAsDemo(UserRole role) async {
    final roleStr = role == UserRole.inspector ? 'inspector' : 'consumer';
    try {
      final res = await http.post(
        Uri.parse(ApiConstants.demoLoginUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'role': roleStr}),
      ).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as Map<String, dynamic>;
        _token = data['access_token'] as String?;
        _currentUser = UserProfile.fromJson(data);
        return _currentUser!;
      } else {
        final data = jsonDecode(res.body) as Map<String, dynamic>?;
        final msg = data?['detail'] ?? 'Demo login failed (${res.statusCode})';
        throw Exception(msg);
      }
    } catch (e) {
      if (e is Exception && !e.toString().contains('ClientException') && !e.toString().contains('SocketException')) {
        rethrow;
      }
      throw Exception('Could not connect to MetroScan server at ${ApiConstants.baseUrl}. Please ensure backend is running.');
    }
  }

  @override
  Future<void> logout() async {
    _currentUser = null;
    _token = null;
  }
}
