import 'package:flutter/material.dart';

/// AppColors defines the exact palette specified for the VisionX application.
/// 
/// Palette:
/// - Dry Sage: #CCD5AE (Primary accents, highlights)
/// - Beige: #E9EDC9 (Secondary surfaces)
/// - Cornsilk: #FEFAE0 (Main light-mode background)
/// - Papaya Whip: #FAEDCD (Cards, input backgrounds)
/// - Light Bronze: #D4A373 (Primary buttons, emphasis)
class AppColors {
  AppColors._();

  // Core Theme Palette
  static const Color drySage = Color(0xFFCCD5AE);
  static const Color beige = Color(0xFFE9EDC9);
  static const Color cornsilk = Color(0xFFFEFAE0);
  static const Color papayaWhip = Color(0xFFFAEDCD);
  static const Color lightBronze = Color(0xFFD4A373);

  // Light Mode Complements
  static const Color lightBackground = cornsilk;
  static const Color lightSurfaceCard = papayaWhip;
  static const Color lightSurfaceSecondary = beige;
  static const Color lightInputBackground = Color(0xFFFBF4DF);
  static const Color lightInputBorder = Color(0xFFE5DECB);
  static const Color lightTextPrimary = Color(0xFF282A24);
  static const Color lightTextSecondary = Color(0xFF6B705C);
  static const Color lightTextMuted = Color(0xFF8F9480);
  static const Color lightButtonText = Color(0xFF221C14);
  static const Color lightDivider = Color(0xFFE5DEC8);

  // Dark Mode Complements (Thoughtfully harmonized with the organic palette)
  static const Color darkBackground = Color(0xFF141613);
  static const Color darkSurfaceCard = Color(0xFF1D211C);
  static const Color darkSurfaceSecondary = Color(0xFF252A23);
  static const Color darkInputBackground = Color(0xFF222720);
  static const Color darkInputBorder = Color(0xFF333A2F);
  static const Color darkTextPrimary = Color(0xFFF7F8F4);
  static const Color darkTextSecondary = Color(0xFFA3A99B);
  static const Color darkTextMuted = Color(0xFF737A6B);
  static const Color darkButtonText = Color(0xFF1C1813);
  static const Color darkDivider = Color(0xFF2C3228);

  // Status & Feedback Colors
  static const Color error = Color(0xFFC85A54);
  static const Color success = Color(0xFF588157);
}
