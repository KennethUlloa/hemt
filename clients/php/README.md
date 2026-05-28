# HEMT Laravel Mail Transport

A custom Laravel mail transport that sends emails to a [HEMT](https://github.com/your-org/hemt) server for capture and inspection.

## Installation

Copy `src/HemtTransport.php` into your Laravel app — for example `app/Mail/HemtTransport.php`.

The class uses Laravel's built-in `Illuminate\Support\Facades\Http` facade, so no extra Composer dependencies are needed.

## Configuration

### 1. Register the transport

In `config/mail.php`, add a new mailer:

```php
'mailers' => [
    // ... other mailers ...

    'hemt' => [
        'transport' => 'hemt',
        'token' => env('HEMT_API_KEY'),
        'base_url' => env('HEMT_ENDPOINT'),
    ],
],
```

### 2. Set your `.env` variables

```env
HEMT_API_KEY=et_abc123...
HEMT_ENDPOINT=http://localhost:5000/api/v1/incoming-mail
```

### 3. Extend the mail system

In `AppServiceProvider::boot()` (or a dedicated service provider):

```php
use Illuminate\Support\Facades\Mail;
use App\Mail\HemtTransport;

public function boot(): void
{
    Mail::extend('hemt', function (array $config) {
        return new HemtTransport(
            token: $config['token'],
            baseUrl: $config['base_url'],
        );
    });
}
```

## Usage

Use the mailer like any other Laravel mailer:

```php
Mail::mailer('hemt')
    ->to('user@example.com')
    ->from('app@myapp.com')
    ->subject('Hello from HEMT')
    ->text('Plain text body')
    ->send();
```

Or with a Mailable class:

```php
class OrderShipped extends Mailable
{
    public function build(): void
    {
        $this->mailer('hemt')
            ->from('orders@myapp.com')
            ->subject('Order Shipped')
            ->text('Your order has shipped.');
    }
}
```

Set `hemt` as the default mailer in `config/mail.php`:

```php
'default' => env('MAIL_MAILER', 'hemt'),
```

Then send without specifying the mailer:

```php
Mail::to('user@example.com')->send(new OrderShipped());
```

## Attachments

Attachments are forwarded to HEMT as file uploads and work with both `attach()` and the Mailable `attachment()` method:

```php
Mail::mailer('hemt')
    ->to('user@example.com')
    ->subject('With attachment')
    ->text('See attached file.')
    ->attach(storage_path('app/report.pdf'))
    ->send();
```

## License

MIT
