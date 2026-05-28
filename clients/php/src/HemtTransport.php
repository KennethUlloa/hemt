<?php

namespace App\Mail\Transport;

use Illuminate\Support\Facades\Http;
use Symfony\Component\Mailer\Envelope;
use Symfony\Component\Mailer\SentMessage;
use Symfony\Component\Mailer\Transport\AbstractTransport;
use Symfony\Component\Mime\Address;
use Symfony\Component\Mime\Email;

class HemtTransport extends AbstractTransport
{
    public function __construct(
        protected string $baseUrl,
        protected string $token,
    ) {
        parent::__construct();
    }

    protected function doSend(SentMessage $message): void
    {
        $original = $message->getOriginalMessage();

        if (!$original instanceof Email) {
            return;
        }

        $to = collect($original->getTo())
            ->map(fn(Address $a) => $a->getAddress())
            ->implode(',');

        $from = collect($original->getFrom())
            ->map(fn(Address $a) => $a->getAddress())
            ->implode(',');

        $request = Http::withToken($this->token)->asMultipart();

        foreach ($original->getAttachments() as $attachment) {
            $body = $attachment->getBody();

            if (is_resource($body)) {
                $body = stream_get_contents($body);
            }

            $request->attach(
                'attachment',
                $body,
                $attachment->getPreparedHeaders()
                    ->getHeaderParameter('Content-Disposition', 'filename')
            );
        }

        $response = $request->post(
            rtrim($this->baseUrl, '/') . '/api/v1/incoming-mail',
            [
                'to' => $to,
                'from' => $from,
                'subject' => $original->getSubject(),
                'body_html' => $original->getHtmlBody(),
                'body_text' => $original->getTextBody(),
            ]
        );

        $response->throw();
    }

    public function __toString(): string
    {
        return 'hemt';
    }
}
