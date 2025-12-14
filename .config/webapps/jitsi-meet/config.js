/* eslint-disable comma-dangle, no-unused-vars, no-var, prefer-template, vars-on-top */
// /qompassai/dotfiles/.config/webapps/jits-meet/config.js
// Qompass AI Jitsi-Meet WebApp Config
// Copyright (C) 2025 Qompass AI, All rights reserved
//////////////////////////////////////////////////////
var subdir = '<!--# echo var="subdir" default="" -->';
var subdomain = '<!--# echo var="subdomain" default="" -->';
if (subdomain) {
    subdomain = subdomain.substr(0, subdomain.length - 1).split('.')
        .join('_')
        .toLowerCase() + '.';
}
if (subdir.startsWith('<!--')) {
    subdir = '';
}
if (subdomain.startsWith('<!--')) {
    subdomain = '';
}
var enableJaaS = false;
var config = {

    hosts: {
        domain: 'jitsi-meet.example.com',
        authdomain: 'jitsi-meet.example.com',
        muc: 'conference.' + subdomain + 'jitsi-meet.example.com',
    },
    bosh: 'https://jitsi-meet.example.com/' + subdir + 'http-bind',
    websocket: 'wss://jitsi-meet.example.com/' + subdir + 'xmpp-websocket',
    websocketKeepAliveUrl: 'https://jitsi-meet.example.com/' + subdir + '_unlock',

    preferBosh: false,
    focusUserJid: 'focus@auth.jitsi-meet.example.com',
    conferenceRequestUrl:
        'https://<!--# echo var="http_host" default="jitsi-meet.example.com" -->/' + subdir + 'conference-request/v1',

    bridgeChannel: {
        ignoreDomain: 'example.com',
        preferSctp: false
    },

    testing: {
        assumeBandwidth: true,
        electronUseGetDisplayMedia: false,
        enableCodecSelectionAPI: false,
        p2pTestMode: false,
        testMode: false,
        noAutoPlayVideo: false,
        skipInterimTranscriptions: false,
        dumpTranscript: false,
        debugAudioLevels: true,
        failICE: true,
    },
    disableModeratorIndicator: false,
    disableReactions: true,
    disableReactionsModeration: false,
    disablePolls: false,
    disableSelfDemote: false,
    disableSelfView: false,
    disableSelfViewSettings: false,
    screenshotCapture: {
        enabled: false,
        mode: 'recording',
    },
    webrtcIceUdpDisable: false,
    webrtcIceTcpDisable: false,
    disableAudioLevels: false,
    audioLevelsInterval: 200,
    enableNoAudioDetection: true,
    enableSaveLogs: false,
    disableShowMoreStats: true,
    enableNoisyMicDetection: true,
    startAudioOnly: false,
    startAudioMuted: 10,
    startWithAudioMuted: false,
    startSilent: false,
    enableOpusRed: false,
    audioQuality: {
        stereo: false,
        opusMaxAverageBitrate: 510000,
        enableOpusDtx: false,
    },
    //   - https://meet.example.com/libs/krisp/krisp.mjs
    //   - https://meet.example.com/libs/krisp/models/model_8.kw
    //   - https://meet.example.com/libs/krisp/models/model_nc.kw
    //   - https://meet.example.com/libs/krisp/models/model_bvc.kw
    //   - https://meet.example.com/libs/krisp/assets/bvc-allowed.txt
    //   - https://meet.example.com/libs/krisp/assets/bvc-allowed-ext.txt
    //   - https://meet.example.com/libs/krisp/models/model_inbound_8.kw
    //   - https://meet.example.com/libs/krisp/models/model_inbound_16.kw
    noiseSuppression: {
        krisp: {
            enabled: false,
            logProcessStats: false,
            debugLogs: false,
            useBVC: false,
            bufferOverflowMS: 1000,
            inboundModels: {
                modelInbound8: 'model_inbound_8.kef',
                modelInbound16: 'model_inbound_16.kef',
            },
            preloadInboundModels: {
                modelInbound8: 'model_inbound_8.kef',
                modelInbound16: 'model_inbound_16.kef',
            },
            preloadModels: {
                modelBVC: 'model_bvc.kef',
                model8: 'model_8.kef',
                modelNC: 'model_nc_mq.kef',
            },
            models: {
                modelBVC: 'model_bvc.kef',
                model8: 'model_8.kef',
                modelNV: 'model_nc_mq.kef',
            },
            bvc: {
                allowedDevices: 'bvc-allowed.txt',
                allowedDevicesExt: 'bvc-allowed-ext.txt',
            }
        },
    },
    cameraFacingMode: 'user',
    resolution: 720,
    raisedHands: {
        disableLowerHandByModerator: false,
        disableLowerHandNotification: true,
        disableNextSpeakerNotification: false,
        disableRemoveRaisedHandOnFocus: false,
    },
    speakerStats: {
        disabled: false,
        disableSearch: false,
        order: [
            'role',
            'name',
            'hasLeft',
        ],
    },
    speakerStatsOrder: [
        'role',
        'name',
        'hasLeft',
    ],
    maxFullResolutionParticipants: 2,
    constraints: {
        video: {
            height: {
                ideal: 720,
                max: 720,
                min: 240,
            },
        },
    },
    disableSimulcast: false,
    startVideoMuted: 10,
    startWithVideoMuted: false,
    desktopSharingFrameRate: {
        min: 5,
        max: 5,
    },
    screenShareSettings: {
        desktopPreferCurrentTab: false,
        desktopSystemAudio: 'include',
        desktopSurfaceSwitching: 'include',
        desktopDisplaySurface: undefined,
        desktopSelfBrowserSurface: 'exclude'
    },
    dropbox: {
        appKey: '<APP_KEY>',
        redirectURI:
            'https://jitsi-meet.example.com/subfolder/static/oauth.html',
    },
    recordings: {
        recordAudioAndVideo: true,
        suggestRecording: true,
        showPrejoinWarning: true,
        showRecordingLink: true,
        requireConsent: true,
    },
    recordingService: {
        enabled: false,
        sharingEnabled: false,
        hideStorageWarning: false,
    },
    fileRecordingsServiceEnabled: false,
    fileRecordingsServiceSharingEnabled: false,
    localRecording: {
        disable: false,
        notifyAllParticipants: false,
        disableSelfRecording: false,
    },
    liveStreaming: {
        enabled: false,
        termsLink: 'https://www.youtube.com/t/terms',
        dataPrivacyLink: 'https://policies.google.com/privacy',
        validatorRegExpString: '^(?:[a-zA-Z0-9]{4}(?:-(?!$)|$)){4}',
        helpLink: 'https://jitsi.org/live'
    },
    transcription: {
        enabled: false,
        translationLanguages: ['en', 'es', 'fr', 'ro'],
        translationLanguagesHead: ['en'],

        useAppLanguage: true,
        preferredLanguage: 'en-US',
        autoTranscribeOnRecord: false,
        autoCaptionOnTranscribe: false,
    },
    channelLastN: -1,
    connectionIndicators: {
        autoHide: true,
        autoHideTimeout: 5000,
        disabled: false,
        disableDetails: false,
        inactiveDisabled: false
    },
    startLastN: 1,
    videoQuality: {
        codecPreferenceOrder: ['VP9', 'VP8', 'H264', 'AV1'],
        screenshareCodec: 'AV1',
        mobileScreenshareCodec: 'VP8',
        enableAdaptiveMode: false,
        av1: {
            maxBitratesVideo: {
                low: 100000,
                standard: 300000,
                high: 1000000,
                fullHd: 2000000,
                ultraHd: 4000000,
                ssHigh: 2500000
            },
            scalabilityModeEnabled: true,
            useSimulcast: false,
            useKSVC: true
        },
        h264: {
            maxBitratesVideo: {
                low: 200000,
                standard: 500000,
                high: 1500000,
                fullHd: 3000000,
                ultraHd: 6000000,
                ssHigh: 2500000
            },
            scalabilityModeEnabled: true
        },
        vp8: {
            maxBitratesVideo: {
                low: 200000,
                standard: 500000,
                high: 1500000,
                fullHd: 3000000,
                ultraHd: 6000000,
                ssHigh: 2500000
            },
            scalabilityModeEnabled: false
        },
        vp9: {
            maxBitratesVideo: {
                low: 100000,
                standard: 300000,
                high: 1200000,
                fullHd: 2500000,
                ultraHd: 5000000,
                ssHigh: 2500000
            },
            scalabilityModeEnabled: true,
            useSimulcast: false,
            useKSVC: true
        },

        minHeightForQualityLvl: {
            360: 'standard',
            720: 'high',
        },
        mobileCodecPreferenceOrder: ['VP8', 'VP9', 'H264'],
    },

    notificationTimeouts: {
        short: 2500,
        medium: 5000,
        long: 10000,
        extraLong: 60000,
    },
    recordingLimit: {
        limit: 60,
        appName: 'Unlimited recordings APP',
        appURL: 'https://unlimited.recordings.app.com/',
    },
    disableRtx: false,
    disableBeforeUnloadHandlers: true,
    enableTcc: true,
    enableRemb: true,
    enableForcedReload: true,
    useTurnUdp: false,
    enableEncodedTransformSupport: true,
    disableResponsiveTiles: false,
    requireDisplayName: true,
    enableWebHIDFeature: false,
    //welcomePage: {
    //     customUrl: ''
    // },
    lobby: {
        autoKnock: false,
        enableChat: true,
    },
    securityUi: {
        hideLobbyButton: false,
        disableLobbyPassword: false,
    },
    disableShortcuts: false,
    disableInitialGUM: false,
    enableClosePage: false,
    disable1On1Mode: false,
    defaultLocalDisplayName: 'me',
    defaultRemoteDisplayName: 'Fellow Jitster',
    hideDisplayName: false,
    hideDominantSpeakerBadge: false,
    defaultLanguage: 'en',
    disableProfile: false,
    hideEmailInSettings: false,
    roomPasswordNumberOfDigits: 10,
    noticeMessage: '',
    enableCalendarIntegration: false,
    notifyOnConferenceDestruction: true,
    // googleApiApplicationClientID: '<client_id>',
    prejoinConfig: {
        enabled: true,
        hideDisplayName: false,
        hideExtraJoinButtons: ['no-audio', 'by-phone'],
        preCallTestEnabled: false,
        preCallTestICEUrl: ''
    },
    readOnlyName: false,
    openSharedDocumentOnJoin: false,
    enableInsecureRoomNameWarning: false,
    corsAvatarURLs: ['https://www.gravatar.com/avatar/'],
    gravatar: {
        baseUrl: 'https://www.gravatar.com/avatar/',
        disabled: false,
    },
    // inviteAppName: null,
    toolbarButtons: [
        'camera',
        'chat',
        'closedcaptions',
        'desktop',
        'download',
        'embedmeeting',
        'etherpad',
        'feedback',
        'filmstrip',
        'fullscreen',
        'hangup',
        'help',
        'highlight',
        'invite',
        'linktosalesforce',
        'livestreaming',
        'microphone',
        'noisesuppression',
        'participants-pane',
        'profile',
        'raisehand',
        'recording',
        'security',
        'select-background',
        'settings',
        'shareaudio',
        'sharedvideo',
        'shortcuts',
        'stats',
        'tileview',
        'toggle-camera',
        'videoquality',
        'whiteboard',
    ],
    toolbarConfig: {
        initialTimeout: 20000,
        timeout: 4000,
        alwaysVisible: false,
        autoHideWhileChatIsOpen: false,
    },
    mainToolbarButtons: [
        ['microphone', 'camera', 'desktop', 'chat', 'raisehand', 'reactions', 'participants-pane', 'tileview'],
        //     [ 'microphone', 'camera', 'desktop', 'chat', 'raisehand', 'participants-pane', 'tileview' ],
        //     [ 'microphone', 'camera', 'desktop', 'chat', 'raisehand', 'participants-pane' ],
        //     [ 'microphone', 'camera', 'desktop', 'chat', 'participants-pane' ],
        //     [ 'microphone', 'camera', 'chat', 'participants-pane' ],
        //     [ 'microphone', 'camera', 'chat' ],
        //     [ 'microphone', 'camera' ]
    ],
    buttonsWithNotifyClick: [
        'camera',
        {
            key: 'chat',
            preventExecution: false
        },
        {
            key: 'closedcaptions',
            preventExecution: true
        },
        'desktop',
        'download',
        'embedmeeting',
        'end-meeting',
        'etherpad',
        'feedback',
        'filmstrip',
        'fullscreen',
        'hangup',
        'hangup-menu',
        'help',
        {
            key: 'invite',
            preventExecution: false
        },
        'livestreaming',
        'microphone',
        'mute-everyone',
        'mute-video-everyone',
        'noisesuppression',
        'participants-pane',
        'profile',
        {
            key: 'raisehand',
            preventExecution: true
        },
        'recording',
        'security',
        'select-background',
        'settings',
        'shareaudio',
        'sharedvideo',
        'shortcuts',
        'stats',
        'tileview',
        'toggle-camera',
        'videoquality',
        {
            key: 'add-passcode',
            preventExecution: false
        },
        'whiteboard',
    ],
    participantMenuButtonsWithNotifyClick: [
        'allow-video',
        {
            key: 'ask-unmute',
            preventExecution: false
        },
        'conn-status',
        'flip-local-video',
        'grant-moderator',
        {
            key: 'kick',
            preventExecution: true
        },
        {
            key: 'hide-self-view',
            preventExecution: false
        },
        'mute',
        'mute-others',
        'mute-others-video',
        'mute-video',
        'pinToStage',
        'privateMessage',
        {
            key: 'remote-control',
            preventExecution: false
        },
        'send-participant-to-room',
        'verify',
    ],
    // 'microphone', 'camera', 'select-background', 'invite', 'settings'
    hiddenPremeetingButtons: [],
    customParticipantMenuButtons: [],
    customToolbarButtons: [],
    gatherStats: false,
    pcStatsInterval: 10000,
    enableDisplayNameInStats: false,
    enableEmailInStats: false,
    faceLandmarks: {
        enableFaceCentering: false,
        enableFaceExpressionsDetection: false,
        enableDisplayFaceExpressions: false,
        enableRTCStats: false,
        faceCenteringThreshold: 10,
        captureInterval: 1000,
    },
    feedbackPercentage: 100,
    disableThirdPartyRequests: false,
    p2p: {
        enabled: true,
        iceTransportPolicy: 'all',
        mobileCodecPreferenceOrder: ['H264', 'VP8', 'VP9'],
        codecPreferenceOrder: ['VP9', 'VP8', 'H264'],
        screenshareCodec: 'AV1',
        mobileScreenshareCodec: 'VP8',
        backToP2PDelay: 5,
        stunServers: [
            { urls: 'stun:jitsi-meet.example.com:3478' },
            { urls: 'stun:meet-jit-si-turnrelay.jitsi.net:443' },
        ],
    },
    analytics: {
        disabled: false,
        matomoEndpoint: 'https://your-matomo-endpoint/',
        matomoSiteID: '42',
        // amplitudeAPPKey: '<APP_KEY>',
        amplitudeIncludeUTM: false,
        obfuscateRoomName: false,
        rtcstatsEnabled: false,
        rtcstatsStoreLogs: false,
        rtcstatsEndpoint: 'wss://rtcstats-server-pilot.jitsi.net/',
        rtcstatsPollInterval: 10000,
        rtcstatsSendSdp: false,
        // scriptURLs: [
        //      "https://example.com/my-custom-analytics.js",
        // ],
        watchRTCEnabled: false,
    },
    apiLogLevels: ['warn', 'log', 'error', 'info', 'debug'],
    deploymentInfo: {
        shard: "shard1",
        region: "europe",
        userRegion: "asia",
        //  },
        // Possible values:
        // - 'ASKED_TO_UNMUTE_SOUND'
        // - 'E2EE_OFF_SOUND'
        // - 'E2EE_ON_SOUND'
        // - 'INCOMING_MSG_SOUND'
        // - 'KNOCKING_PARTICIPANT_SOUND'
        // - 'LIVE_STREAMING_OFF_SOUND'
        // - 'LIVE_STREAMING_ON_SOUND'
        // - 'NO_AUDIO_SIGNAL_SOUND'
        // - 'NOISY_AUDIO_INPUT_SOUND'
        // - 'OUTGOING_CALL_EXPIRED_SOUND'
        // - 'OUTGOING_CALL_REJECTED_SOUND'
        // - 'OUTGOING_CALL_RINGING_SOUND'
        // - 'OUTGOING_CALL_START_SOUND'
        // - 'PARTICIPANT_JOINED_SOUND'
        // - 'PARTICIPANT_LEFT_SOUND'
        // - 'RAISE_HAND_SOUND'
        // - 'REACTION_SOUND'
        // - 'RECORDING_OFF_SOUND'
        // - 'RECORDING_ON_SOUND'
        // - 'TALK_WHILE_MUTED_SOUND'
        // disabledSounds: [],
        // chromeExtensionBanner: {
        //     url: 'https://chrome.google.com/webstore/detail/jitsi-meetings/kglhbbefdnlheedjiejgomgmfplipfeb',
        //     edgeUrl: 'https://microsoftedge.microsoft.com/addons/detail/jitsi-meetings/eeecajlpbgjppibfledfihobcabccihn',
        //     chromeExtensionsInfo: [
        //             id: 'kglhbbefdnlheedjiejgomgmfplipfeb',
        //             path: 'jitsi-logo-48x48.png',
        //         },
        //         {
        //             id: 'eeecajlpbgjppibfledfihobcabccihn',
        //             path: 'jitsi-logo-48x48.png',
        //        },
        //     ]
        // },
        e2ee: {
            labels: {
                description: '',
                label: '',
                tooltip: '',
                warning: '',
            },
            externallyManagedKey: false,
            disabled: false,
        },
        e2eping: {
            enabled: false,
            numRequests: 5,
            maxConferenceSize: 200,
            maxMessagesPerSecond: 250,
        },
        // _desktopSharingSourceDevice: 'sample-id-or-label',
        deeplinking: {
            desktop: {
                appName: 'Jitsi Meet',
                appScheme: 'jitsi-meet',
                download: {
                    linux:
                        'https://github.com/jitsi/jitsi-meet-electron/releases/latest/download/jitsi-meet-x86_64.AppImage',
                    macos: 'https://github.com/jitsi/jitsi-meet-electron/releases/latest/download/jitsi-meet.dmg',
                    windows: 'https://github.com/jitsi/jitsi-meet-electron/releases/latest/download/jitsi-meet.exe'
                },
                enabled: false
            },
            disabled: false,
            hideLogo: false,
            ios: {
                appName: 'Jitsi Meet',
                appScheme: 'org.jitsi.meet',
                downloadLink: 'https://itunes.apple.com/us/app/jitsi-meet/id1165103905',
                dynamicLink: {
                    apn: 'org.jitsi.meet',
                    appCode: 'w2atb',
                    customDomain: undefined,
                    ibi: 'com.atlassian.JitsiMeet.ios',
                    isi: '1165103905'
                }
            },
            android: {
                appName: 'Jitsi Meet',
                appScheme: 'org.jitsi.meet',
                downloadLink: 'https://play.google.com/store/apps/details?id=org.jitsi.meet',
                appPackage: 'org.jitsi.meet',
                fDroidUrl: 'https://f-droid.org/en/packages/org.jitsi.meet/',
                dynamicLink: {
                    apn: 'org.jitsi.meet',
                    appCode: 'w2atb',
                    customDomain: undefined,
                    ibi: 'com.atlassian.JitsiMeet.ios',
                    isi: '1165103905'
                }
            }
        },
        legalUrls: {
            helpCentre: 'https://web-cdn.jitsi.net/faq/meet-faq.html',
            privacy: 'https://jitsi.org/meet/privacy',
            terms: 'https://jitsi.org/meet/terms'
        },
        disableLocalVideoFlip: false,
        doNotFlipLocalVideo: false,
        disableInviteFunctions: true,
        doNotStoreRoom: true,
        deploymentUrls: {
            userDocumentationURL: 'https://docs.example.com/video-meetings.html',
            downloadAppsUrl: 'https://docs.example.com/our-apps.html',
        },
        remoteVideoMenu: {
            disabled: true,
            disableDemote: true,
            disableKick: true,
            disableGrantModerator: true,
            disablePrivateChat: true,
        },
        salesforceUrl: 'https://api.example.com/',
        disableRemoteMute: true,
        //{
        groupChatRequiresPermission: false,
        pollCreationRequiresPermission: false,
        inviteDomain: 'example-company.org',
        backgroundColor: '#fff',
        backgroundImageUrl: 'https://example.com/background-img.png',
        logoClickUrl: 'https://example-company.org',
        logoImageUrl: 'https://example.com/logo-img.png',
        avatarBackgrounds: ['url(https://example.com/avatar-background-1.png)', '#FFF'],
        premeetingBackground: 'url(https://example.com/premeeting-background.png)',
        virtualBackgrounds: ['https://example.com/img.jpg'],
        customIcons: {
            IconArrowUp: 'https://example.com/arrow-up.svg',
            IconDownload: 'https://example.com/download.svg',
            IconRemoteControlStart: 'https://example.com/remote-start.svg',
        },
        customTheme: {
            palette: {
                ui01: "orange !important",
                ui02: "maroon",
                surface02: 'darkgreen',
                ui03: "violet",
                ui04: "magenta",
                ui05: "blueviolet",
                action01: 'green',
                action01Hover: 'lightgreen',
                disabled01: 'beige',
                success02: 'cadetblue',
                action02Hover: 'aliceblue',
            },
            typography: {
                labelRegular: {
                    fontSize: 25,
                    lineHeight: 30,
                    fontWeight: 500,
                }
            }
        }
    },
    dynamicBrandingUrl: '',
    sharedVideoAllowedURLDomains: [],
    participantsPane: {
        enabled: true,
        hideModeratorSettingsTab: false,
        hideMoreActionsButton: false,
        hideMuteAllButton: false,
    },
    breakoutRooms: {
        hideAddRoomButton: false,
        hideAutoAssignButton: false,
        hideJoinRoomButton: false,
    },
    disableVirtualBackground: false,
    disableAddingBackgroundImages: false,
    backgroundAlpha: 1,
    moderatedRoomServiceUrl: 'https://moderated.jitsi-meet.example.com',
    disableTileView: true,
    disableTileEnlargement: true,
    conferenceInfo: {
        alwaysVisible: ['recording', 'raised-hands-count'],
        autoHide: [
            'subject',
            'conference-timer',
            'participants-count',
            'e2ee',
            'video-quality',
            'insecure-room',
            'highlight-moment',
            'top-panel-toggle',
        ]
    },
    hideConferenceSubject: false,
    hideConferenceTimer: false,
    hideRecordingLabel: false,
    hideParticipantsStats: true,
    subject: 'Conference Subject',
    localSubject: 'Conference Local Subject',
    useHostPageLocalStorage: true,
    etherpad_base: 'https://your-etherpad-installati.on/p/',
    //{"countryCode":"US","tollFree":false,"formattedNumber":"+1 123-456-7890"}
    tokenAuthUrl:
        'https://myservice.com/auth/{room}?code_challenge_method=S256&code_challenge={code_challenge}&state={state}',
    tokenLogoutUrl: 'https://myservice.com/logout',
    tokenAuthUrlAutoRedirect: false,
    tokenRespectTenant: false,
    // Valid values are "phone", "room", "sip", "user", "videosipgw" and "email"
    peopleSearchQueryTypes: ["user", "email"],
    peopleSearchUrl: "https://myservice.com/api/people",
    inviteServiceUrl: "https://myservice.com/api/invite",
    peopleSearchTokenLocation: "mytoken",
    visitors: {
        enableMediaOnPromote: {
            audio: true,
            video: true
        },
    },
    desktopSharingSources: ['screen', 'window'],
    disableAEC: true,
    disableAGC: true,
    disableAP: true,
    disableNS: true,
    displayJids: true,
    enableTalkWhileMuted: true,
    forceTurnRelay: true,
    // List of undocumented settings used in jitsi-meet
    /**
     _immediateReloadThreshold
     deploymentInfo
     dialOutAuthUrl
     dialOutCodesUrl
     dialOutRegionUrl
     disableRemoteControl
     iAmRecorder
     iAmSipGateway
     microsoftApiApplicationClientID
     */
    brandingRoomAlias: null,
    // List of undocumented settings used in lib-jitsi-meet
    /**
     _peerConnStatusOutOfLastNTimeout
     _peerConnStatusRtcMuteTimeout
     avgRtpStatsN
     desktopSharingSources
     disableLocalStats
     hiddenDomain
     hiddenFromRecorderFeatureEnabled
     ignoreStartMuted
     websocketKeepAlive
     websocketKeepAliveUrl
     */
    mouseMoveCallbackInterval: 1000,
    notifications: [
        'connection.CONNFAIL',
        'dialog.cameraConstraintFailedError',
        'dialog.cameraNotSendingData',
        'dialog.kickTitle',
        'dialog.liveStreaming',
        'dialog.lockTitle',
        'dialog.maxUsersLimitReached',
        'dialog.micNotSendingData',
        'dialog.passwordNotSupportedTitle',
        'dialog.recording',
        'dialog.remoteControlTitle',
        'dialog.reservationError',
        'dialog.screenSharingFailedTitle',
        'dialog.serviceUnavailable',
        'dialog.sessTerminated',
        'dialog.sessionRestarted',
        'dialog.tokenAuthFailed',
        'dialog.tokenAuthFailedWithReasons',
        'dialog.transcribing',
        'dialOut.statusMessage',
        'liveStreaming.busy',
        'liveStreaming.failedToStart',
        'liveStreaming.unavailableTitle',
        'lobby.joinRejectedMessage',
        'lobby.notificationTitle',
        'notify.audioUnmuteBlockedTitle',
        'notify.chatMessages',
        'notify.connectedOneMember',
        'notify.connectedThreePlusMembers',
        'notify.connectedTwoMembers',
        'notify.dataChannelClosed',
        'notify.hostAskedUnmute',
        'notify.invitedOneMember',
        'notify.invitedThreePlusMembers',
        'notify.invitedTwoMembers',
        'notify.kickParticipant',
        'notify.leftOneMember',
        'notify.leftThreePlusMembers',
        'notify.leftTwoMembers',
        'notify.linkToSalesforce',
        'notify.localRecordingStarted',
        'notify.localRecordingStopped',
        'notify.moderationInEffectCSTitle',
        'notify.moderationInEffectTitle',
        'notify.moderationInEffectVideoTitle',
        'notify.moderator',
        'notify.mutedRemotelyTitle',
        'notify.mutedTitle',
        'notify.newDeviceAudioTitle',
        'notify.newDeviceCameraTitle',
        'notify.noiseSuppressionFailedTitle',
        'notify.participantWantsToJoin',
        'notify.participantsWantToJoin',
        'notify.passwordRemovedRemotely',
        'notify.passwordSetRemotely',
        'notify.raisedHand',
        'notify.screenShareNoAudio',
        'notify.screenSharingAudioOnlyTitle',
        'notify.selfViewTitle',
        'notify.startSilentTitle',
        'notify.suboptimalExperienceTitle',
        'notify.unmute',
        'notify.videoMutedRemotelyTitle',
        'notify.videoUnmuteBlockedTitle',
        'prejoin.errorDialOut',
        'prejoin.errorDialOutDisconnected',
        'prejoin.errorDialOutFailed',
        'prejoin.errorDialOutStatus',
        'prejoin.errorStatusCode',
        'prejoin.errorValidation',
        'recording.busy',
        'recording.failedToStart',
        'recording.unavailableTitle',
        'toolbar.noAudioSignalTitle',
        'toolbar.noisyAudioInputTitle',
        'toolbar.talkWhileMutedPopup',
        'transcribing.failed',
    ],
    disabledNotifications: [],
    disableFilmstripAutohiding: false,
    filmstrip: {
        disabled: false,
        disableResizable: false,
        disableStageFilmstrip: false,
        stageFilmstripParticipants: 1,
        disableTopPanel: false,

        minParticipantCountForTopPanel: 50,
    },
    tileView: {
        disabled: false,
        numberOfVisibleTiles: 25,
    },
    disableChatSmileys: false,
    giphy: {
        enabled: false,
        sdkKey: '',
        displayMode: 'all',
        tileTime: 5000,
        rating: 'pg',
    },
    logging: {
        defaultLogLevel: 'trace',
        //disableLogCollector: true,
        loggers: {
            'modules/RTC/TraceablePeerConnection.js': 'info',
            'modules/xmpp/strophe.util.js': 'log',
        },
    },
    defaultLogoUrl: 'images/watermark.svg',
    whiteboard: {
        enabled: true,
        collabServerBaseUrl: 'https://excalidraw-backend.example.com',
        userLimit: 25,
        limitUrl: 'https://example.com/blog/whiteboard-limits',
    },
    watchRTCConfigParams: {
        //         rtcApiKey: string;
        //         rtcRoomId?: string;
        //         rtcPeerId?: string;
        //         rtcTags?: string[];
        //         /** { "key1": "value1", "key2": "value2"} */
        //         keys?: any;
        //         debug?: boolean;
        //         rtcToken?: string;
        //         /**
        //          * @deprecated No longer needed. Use "proxyUrl" instead.
        //          */
        //         wsUrl?: string;
        //         proxyUrl?: string;
        //         console?: {
        //             level: string;
        //             override: boolean;
        //         };
        //         allowBrowserLogCollection?: boolean;
        //         collectionInterval?: number;
        //         logGetStats?: boolean;
    },
    hideLoginButton: true,
    disableCameraTintForeground: false,
};
if (enableJaaS) {
    config.dialInNumbersUrl = 'https://conference-mapper.jitsi.net/v1/access/dids';
    config.dialInConfCodeUrl = 'https://conference-mapper.jitsi.net/v1/access';
    config.roomPasswordNumberOfDigits = 10;
}
