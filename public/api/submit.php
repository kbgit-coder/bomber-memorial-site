<?php
// Form submission handler for Bomber Command Memorial Register
// Receives contact form and verification submissions
// Sends Telegram notification, stores to local JSON log

header('Content-Type: application/json');

// CORS
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
$allowed = ['https://bombermemorial.co.uk', 'https://www.bombermemorial.co.uk', 'https://staging.bombermemorial.co.uk'];
if (in_array($origin, $allowed)) {
    header("Access-Control-Allow-Origin: $origin");
}
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: POST, OPTIONS');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$TELEGRAM_BOT_TOKEN = '8122161069:AAEnyTojJYJ4ihFMpecVFwJRiWntEpK-25s';
$TELEGRAM_CHAT_ID = '7897654941';

$input = json_decode(file_get_contents('php://input'), true);
if (!$input) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

$type = $input['type'] ?? 'contact';
$email = filter_var($input['email'] ?? '', FILTER_VALIDATE_EMAIL);
if (!$email) {
    http_response_code(400);
    echo json_encode(['error' => 'Valid email required']);
    exit;
}

// Store submission
$logDir = __DIR__ . '/../_data';
if (!is_dir($logDir)) mkdir($logDir, 0750, true);
$logFile = $logDir . '/submissions.jsonl';
$entry = array_merge($input, ['timestamp' => date('c'), 'ip' => $_SERVER['REMOTE_ADDR'] ?? '']);
file_put_contents($logFile, json_encode($entry) . "\n", FILE_APPEND | LOCK_EX);

// Build Telegram message
if ($type === 'verify') {
    $msg = "📍 Location verification — Bomber Memorial\n\n"
        . "Memorial: " . ($input['memorial_title'] ?? $input['memorial_id'] ?? 'unknown') . "\n"
        . "ID: " . ($input['memorial_id'] ?? '') . "\n"
        . "From: " . ($input['name'] ?? 'Anonymous') . " <$email>\n\n"
        . "Evidence/source:\n" . ($input['source'] ?? '') . "\n"
        . ($input['corrected_lat'] ? "\nCorrected lat: {$input['corrected_lat']}" : '')
        . ($input['corrected_lng'] ? "\nCorrected lng: {$input['corrected_lng']}" : '');
} else {
    $msg = "📬 New contact — Bomber Memorial\n\n"
        . "Name: " . ($input['name'] ?? 'Not provided') . "\n"
        . "Email: $email\n"
        . ($input['message'] ? "Message: {$input['message']}\n" : '');
}

// Send Telegram
$ch = curl_init("https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage");
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode(['chat_id' => $TELEGRAM_CHAT_ID, 'text' => $msg]),
    CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 5,
]);
curl_exec($ch);
curl_close($ch);

echo json_encode(['success' => true, 'message' => 'Thank you for your contribution.']);
