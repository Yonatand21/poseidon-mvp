#include "PoseidonBridge.h"

#include "WebSocketsModule.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

void UPoseidonBridge::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    if (!FModuleManager::Get().IsModuleLoaded(TEXT("WebSockets")))
    {
        FModuleManager::Get().LoadModule(TEXT("WebSockets"));
    }
}

void UPoseidonBridge::Deinitialize()
{
    if (Socket.IsValid() && Socket->IsConnected())
    {
        Socket->Close();
    }
    Socket.Reset();
    Super::Deinitialize();
}

void UPoseidonBridge::Connect(const FString& ServerUrl)
{
    CachedServerUrl = ServerUrl.IsEmpty() ? TEXT("ws://localhost:9090") : ServerUrl;

    Socket = FWebSocketsModule::Get().CreateWebSocket(CachedServerUrl);

    Socket->OnConnected().AddUObject(this, &UPoseidonBridge::OnSocketConnected);
    Socket->OnConnectionError().AddUObject(this, &UPoseidonBridge::OnSocketConnectionError);
    Socket->OnClosed().AddUObject(this, &UPoseidonBridge::OnSocketClosed);
    Socket->OnMessage().AddUObject(this, &UPoseidonBridge::OnSocketMessage);

    Socket->Connect();
}

bool UPoseidonBridge::IsConnected() const
{
    return Socket.IsValid() && Socket->IsConnected();
}

void UPoseidonBridge::Subscribe(const FString& Topic, const FString& MessageType)
{
    if (!IsConnected())
    {
        PendingSubscriptions.Add({Topic, MessageType});
        return;
    }

    TSharedRef<FJsonObject> Payload = MakeShared<FJsonObject>();
    Payload->SetStringField(TEXT("op"), TEXT("subscribe"));
    Payload->SetStringField(TEXT("topic"), Topic);
    Payload->SetStringField(TEXT("type"), MessageType);

    FString Out;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Out);
    FJsonSerializer::Serialize(Payload, Writer);

    Socket->Send(Out);
}

void UPoseidonBridge::OnSocketConnected()
{
    UE_LOG(LogTemp, Log, TEXT("[PoseidonBridge] connected to %s"), *CachedServerUrl);
    for (const auto& Sub : PendingSubscriptions)
    {
        Subscribe(Sub.Get<0>(), Sub.Get<1>());
    }
    PendingSubscriptions.Empty();
}

void UPoseidonBridge::OnSocketConnectionError(const FString& Error)
{
    UE_LOG(LogTemp, Warning, TEXT("[PoseidonBridge] connection error: %s"), *Error);
}

void UPoseidonBridge::OnSocketClosed(int32 StatusCode, const FString& Reason, bool bWasClean)
{
    UE_LOG(LogTemp, Log, TEXT("[PoseidonBridge] closed code=%d clean=%d reason=%s"),
           StatusCode, bWasClean ? 1 : 0, *Reason);
}

void UPoseidonBridge::OnSocketMessage(const FString& Message)
{
    // Dispatched on the WebSocket thread; forward to the game thread.
    AsyncTask(ENamedThreads::GameThread, [WeakThis = TWeakObjectPtr<UPoseidonBridge>(this), Message]()
    {
        if (UPoseidonBridge* Strong = WeakThis.Get())
        {
            Strong->OnMessage.Broadcast(Message);
        }
    });
}
